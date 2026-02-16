#ifndef COMMON_H
#define COMMON_H

#include <stdint.h>
#include <pthread.h> // RW_Lock: 초기화할 때 shared 설정
#include <semaphore.h> //sem: 초기화할 때 shared 설정
#include <fcntl.h> // O_CREAT, O_RDWR
#include <sys/mman.h> // mmap, munmap
#include <unistd.h> // ftruncate, close

#define SHM_NAME "/shm_jam"
#define SHM_SIZE sizeof(struct jam_data)
//#define SHM_KEY ftok("/common.h", 'A')  //ftok("실행중인파일경로", '문자') 

struct jam_data {
    pthread_rwlock_t rwlock;
    sem_t sem_data;
    double signal_speed;
    uint32_t crc32;
    int is_running;
}__attribute__((aligned(8)));

//crc32 함수 계산
static inline uint32_t calculate_crc(double data){

    uint32_t val = *(uint32_t*)&data;
    return (val >> 1)^0xEDB88320^(val << 5);
}

#endif