// 제어 프로세스 

#define _GNU_SOURCE // 코어
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#include <pthread.h>
#include "common.h"

int shmid;
struct jam_data *ptr = NULL;


void clean_shm(int sig){
    if (sig == SIGSEGV){
        printf("[Error] SegmentFault 감지. 자원 정리 및 비정상 종료. (Signal=%d)\n", sig);
        shm_unlink(SHM_NAME);
        exit(1);
    }

    else if (sig == SIGINT){
        shm_unlink(SHM_NAME); 
    // 공유메모리 객체의 이름을 시스템에서 제거함. 인자:  메모리 식별자(이름)ex) "/my_shm"
    // 이제 SHM_NAME으로 공유메모리 자원에 새로 연결하는 건 안 됨. 기존에 연결된 것들은 계쏙 쓸 수 있음 
    // (이름만 없어지고 프로세스와 공유메모리 영역의 연결은 그대로인 상태)
    // 연결도 끊으려면 munmap 함 (분석 플세스에서)
        printf("\n[Control] 강제 중단. 자원 정리 및 정상 종료. (Signal= %d)\n", sig);
        exit(0);
    }

    else if (sig == 0){
        shm_unlink(SHM_NAME);
        printf("[Control] 정상 종료. 자원 정리 및 정상 종료. (Signal=%d)\n", sig);
        exit(0);

    }
}

int main(){
    signal(SIGSEGV, clean_shm); // 세그먼트 폴트 발생시 경고
    signal(SIGINT, clean_shm); //강제종료(SIGnal INTerrupt) 시 clean_shm 실행
//signal 함수를 쓰면 SIGINT 인자는 clean_shm 에 자동으로 들어감.
   
// ------1. CPU Affinity 설정 (1번 코어)
    cpu_set_t mask;
    CPU_ZERO(&mask);
    CPU_SET(1, &mask);
    sched_setaffinity(0, sizeof(mask), &mask); // 첫번째 인자: 1번 코어와 연결할 프로세스의 주소.
    printf("[Control] 1번 코어에서 제어 루틴 가동\n");


// ------2. POSIX 공유 메모리 생성
    int fd = shm_open(SHM_NAME, O_CREAT|O_RDWR, 0666); // 공유메모리에 대한 권한 설정
    if (fd == -1) {perror("[Master]shm_open error"); exit(1);}

    // 2. 크기 설정 (처음 생성하면 크기가 0이라서 꼭 해야 함)
    if (ftruncate(fd, sizeof(struct jam_data))==-1)
    { perror("[Master]ftruncate error"); exit(1); } // 공유메모리 크기 설정과 에러잡기 동시에.
    
    // ------3. 메모리에 올리기(매핑)
    ptr = (struct jam_data *)mmap(NULL, sizeof(struct jam_data), PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0); 
    if (ptr == MAP_FAILED) {perror("mmap error");  exit(1); }
    // mmap 함수는 실패하면 NULL 이나 -1 이 아니라 (void *)-1 을 반환한다. 이 값의 매크로가 MAP_FAILED 임.
    // 공유메모리에 올릴 프로그램에 대한 설정
    // 시작주소, 프로그램크기, 보호모드, 공유설정 _SHARED, _PRIVATE, fd, 오프셋(공유메모리 중 쓰기 시작할 지점)
    // MAP_SHARED : 메모리 내용을 바꿨을 때 다른 프로세스들이 실시간으로 변화를 알 수 있게 할 것인지 설정. / IPC 는 무조건 MAP_SHARED
    // MAP_PRIVATE : 메모리 내용을 바꿔도 실제 공유메모리 변화X. 프로세스는 본인 개인 메모리에 복사본을 만들어서 쓴다. -> 세마포어 작동 및 업데이트 확인 불가.


    // attr 이라는 이름: 어떤 객체가 어떻게 동작할지 결정하는 세부 설정값. 
    // ------4. 동기화 객체 초기화 (프로세스 공유설정)
    pthread_rwlockattr_t rw_attr; // RW-Lock의 설정 시트 생성
    pthread_rwlockattr_init(&rw_attr); // RW-Lock 의 속성 객체 초기화.
    pthread_rwlockattr_setpshared(&rw_attr, PTHREAD_PROCESS_SHARED); // 잠금의 공유범위를 결정함.
    pthread_rwlock_init(&(ptr->rwlock), &rw_attr); // 위에서 설정한 속성 ew_attr을 바탕으로 실제 ptr->rwlock 을 생성함. 이변수를 통해 읽기/쓰기 권한 제어가능.

    sem_init(&(ptr->sem_data), 1, 0); // 
    // 세마포어 공유범위 0: 같은 프로세스 내 스레드끼리 n(>1): 다른 프로세스 간. 1이면 뮤텍스처럼 동작함. (Mutual Exclusion)
    // 세마포어 초깃값: 다른 프로세스가 공유메모리에 데이터를 쓴 뒤 sem_post을 해주기 전까지는 잠들어 있다.
    ptr->is_running = 1;
    printf("[Master][Control Process] 감시 및 제어루틴\n");


    while(ptr->is_running){
        sem_wait(&(ptr->sem_data)); // generator 나 attacker 에서 신호가 올 때까지 대기한다.
// 세마포어 값이 0보다 크면 1을 감소시키고 즉시 통과, 0이면 기다림. 
        pthread_rwlock_rdlock(&(ptr->rwlock)); // 읽기 전용 잠금 획득. 다른 프로세스들도 rdlock 을 잡고 읽는 것은 허용. BUT wrlock 시도하면 대기 해야함. 
// 읽는 도중에 데이터가 바뀌어서 생기는 오염 현상 방지.
        uint32_t expected_crc = calculate_crc(ptr->signal_speed);
        if (ptr->crc32 != expected_crc){
// 송신측: 속도+CRC 보냄 수신측: 속도를 받아서 읽고 CRC 계산함. 계산결과(expected_crc)와 받은 CRC(ptr->crc32) 가 같으면 정상.
// 보통 속도만 변조하거나 속도+CRC 를 변조해서 보낸다. 후자의 경우에는 시간 변수가 들어가야 재밍 탐지 가능. 
// ? 재밍탐지: 송신과 수신 전파 차이를 이용한 거리 산출? 시간? 어떻게 측정?
            printf("[Master][ALERT] 재밍 의심 : 변조 의심 데이터 감지! (Speed: %.2f, Expected CRC: %u, Recv CRC: %u)\n", ptr->signal_speed, ptr->crc32, expected_crc);
        }
        else{
            printf("[Master][CONTROL] 정상 신호 확인 : %.2f km/h \n", ptr->signal_speed);

        }

        pthread_rwlock_unlock(&(ptr->rwlock)); // 읽기 쓰기 둘다 잠금 해제?
// 읽기 전용 접근 잠금 해제. 다음 데이터가 데드락에 빠지지 않으려면 반드시 해제해야 함.
// lock 에 맞춰서 unlock 해야 함.
    }
    clean_shm(0); 
    return 0;

}