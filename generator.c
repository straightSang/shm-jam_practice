#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
#include <sys/mman.h>
#include <sched.h> // set_cpu_t, CPU_ZERO, CPU_SET
#include "common.h"

int main(){

    // ---- 1. CPU 설정

    // mask 시트 작성
    cpu_set_t mask;
    CPU_ZERO(&mask); // mask 코어 설정 초기화
    CPU_SET(0, &mask); // 0번 CPU 사용하겠다고 선언 // [0] 첫번째 칸에 1이 들어감.
// 코어가 증가할수록 CPU가 강력하다.
    // CPU 실제 적용
    if (sched_setaffinity(0, sizeof(mask), &mask) == -1){
        perror("[Generator] CPU setting is failed.");
        exit(1);
    }

    printf("[Generator] 0번 코어에서 분석 시작\n");


    // -----2. POSIX 공유 메모리 참조
    // master 에서 이미 생성한 상태여야 함. O_CREAT을 한 프로세스가 권한을 0666 으로설정했어야 함.
    // 혹은 0644, 0640이고, MAster와 Slave 가 같은 계정으로 실행되어야 함.
    //  fd 는 공유메모리 공간에 접근할 수 있는 열쇠. 같은 공유메모리여도 프로세스마다 fd 번호 다름.
    //int fd = shm_open(SHM_NAME, O_RDWR, 0666)
    int fd = shm_open(SHM_NAME, O_RDONLY, 0); // 권한설정 무시,0넣기.
    // 
    // shm_open 은 인자를 3개만 받음. 읽기 전용일 때는 세번째 인자X.
    // shm_open RDONLY라면 mmap의 권한도 맞춰줘야 한다. PROT_READ
    if (fd == -1) {

        perror("[Generator] shm_open is failed.");
        exit(1);

    }

    // ---3. 메모리 매핑
    struct jam_data *ptr = (struct jam_data*)mmap(NULL, sizeof(struct jam_data), PROT_READ, MAP_SHARED, fd, 0); 
    //프로세스가 접근할 수 있는 범위&시작점,접근 크기
    // 읽기권한만 설정함 -> 읽기만 가능. 쓰려고 하는 순간 Segment Fault 발생.

    if (ptr==MAP_FAILED){
        perror("[Generator] mmap is failed");
        exit(1);
    }

    double test_signals[] = {12.5, 45.3, 120.7, 0.0};
    for (int i=0; i<4; i++){
        sleep(2); // 분석 주기 모사????????

        // -----4. WRlock
        pthread_rwlock_wrlock(&(ptr->rwlock)); // relock 잠금 획득

        ptr->signal_speed = test_signals[i];

        printf("[Generator] 데이터 갱신 완료: %.2f (CRC: %u)\n", ptr->signal_speed, ptr->crc32);

        pthread_rwlock_unlock(&(ptr->rwlock));

        // -----5. 신호 전송(Master 해제)
    }
    sem_post(&(ptr->sem_data));
    // 자원 해제
    // munmap: 메모리에접근X 알림.명시성 , 프로그램 확정성(exit(0))전 긴 코드 생성시. , mmap-munmap, open-close 의 관계. 자원할당-해제 맞춤: 버그 예방.
    munmap(ptr, sizeof(struct jam_data)); // munmap 은 분석(자식)프로세스에서 함. shm_unlink는 제어(부모)에서 함.
    close(fd);

    printf("[Generator] 분석 종료.\n");
    return 0;
}