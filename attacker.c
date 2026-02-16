#define _GNU_SOURCE // CPU set 등 스케줄링 기능 이용
#include <stdio.h>
#include <stdlib.h> //
#include <unistd.h> //32비트 정수 고정 등 사용
#include <fcntl.h> // shm_open ?
#include <sys/mman.h> // mmap, munmap, close??
#include <sched.h> // 
#include <pthread.h>
#include "common.h"

int main(){
    cpu_set_t mask;
    CPU_ZERO(&mask);
    CPU_SET(2, &mask);

    if(sched_setaffinity(0, sizeof(mask), &mask)==-1) {// 첫번째 인자: cpu를 사용할 프로세스 ID (0은 현재 자신.)
        perror("[Attacker] CPU setting is failed.");
        exit(1);
    }
    printf("[Attacker] 2번 코어에서 실행 중.\n"
    );

    int fd = shm_open(SHM_NAME, O_RDWR, 0);
    struct jam_data *ptr = (struct jam_data *)mmap(NULL, sizeof(struct jam_data), PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
    if (shm_open(SHM_NAME, O_RDWR, 0666)==-1){
        perror("[Attacker] shm_open is failed (There is no shared memory)");
        exit(1);
    }

    printf("[Attacker] 공격 준비. 3초 후 데이터 변조.\n");
    sleep(3); // <unistd.h>, 초 단위, 3초 동안 프로세스나 스레드 정지시킴.
    // 프로그램의 Generator 가 끝날 때까지 기다린 뒤 MAster에서 검증하기 전에 데이터 바꾸기 모사.
    // 정상작동과 비정상 작동 비교 위함.


    //--------4. 데이터 변조 실행 ---------
    pthread_rwlock_wrlock(&(ptr->rwlock)); // 쓰기 잠금 설정
// 해당 프로세스 말고는 아무도 읽지도 쓰지도 못함. -> Master가 읽지 못하게 한 상태에서 오렴시킨다.
    printf("[Attacker] 데이터 변조 중: 속도를 200.0 으로 변경(CRC 무시)\n");
    ptr->signal_speed = 200; // 속도변조
    // CRC 는 변조하지 않음으로써 데이터 무결성 오류를 유도함. 
    // ?????

    pthread_rwlock_unlock(&(ptr->rwlock));

    // Master/Generator를 깨우기 위한 신호 전송
    sem_post(&(ptr->sem_data));


    printf("[Attacker] 공격 완료. Master의 무결성 검사 확인할 것.\n");


    // 정리
    munmap(ptr, sizeof(struct jam_data)); // 프로세스와 메모리 해제
    close(fd);

    return 0;

}