# 파일이름과 타겟이름(all clean test)이 겹쳐서 발생하는 버그를 막는 방어막.
.PHONY: all clean test
# .으로 시작하는 단어는 지시어임을 의미한다.
# .PHONY 뒤에는 동일한 이름의 파일이 있어도 무시하고 실행할 타겟들의 목록.
# 파일이 아니(가짜)이므로 위의 단어들은 파일검사하지 말라는 의미. 

# 변수 설정
CC = gcc # 컴파일러
CFLAGS = -Wall -o2 # -Wall:경고on  -02:최적화on
LDFLAGS = -lrt -lpthread # POSIX실시간라이브러리, 스레드라이브러리(RW_Lock)


# 빌드 대상 리스트
# 빌드할 대상을 구룹화함. make 명령을 내리면 
# 그룹화된 프로그램들이 순차적으로 컴파일되기 때문에 빌드 누락 방지.
TARGETS = master generator attacker
#TAEGET:결과물 Prerequisites:소스파일 Recipe:(TAP)명령어

# 기본 빌드 규칙
# all, clean, test : 특정동작을 가리키는 타겟.
# 모든실행파일만들기, 빌드 중 생성된 찌꺼기(.o 혹은 실행파일)를 지워 pj 초기화, 빌드후 안내메세지 출력 록은 데스트 스크립트 실행

all: $(TARGETS) # all: make->all->TARGETS 빌드 연쇄명령

# 각 타겟별 빌드 상세 (패턴 규칙 사용)
master: master.c common.h # : 이후로 적힌 master.c 나 common.h 파일들이 수정되면 make가 이를 감지하고 관련된 파일을 모두 다시 빌드한다.
# 타겟파일(새로만들고업데이트할파일이름): 소스파일 / 소스파일이 업데이트되면 반영한다.
# $@: 현재 타겟의 이름 $^: 모든 소스 파일 리스트
	$(CC) $(CFLAGS) -o $@ master.c $(LDFLAGS)
	#컴파일러 경고및최적화 출력파일명=현재타겟이름 소스파일 외부라이브러리함수들link
# 명령어 현재타겟파일 명령어

generator: generator.c common.h
	$(CC) $(CFLAGS) -o $@ generator.c $(LDFLAGS)

attacker: attacker.c common.h 
	$(CC) $(CFLAGS) -o $@ attacker.c $(LDFLAGS)


#정리 규칙
clean:
	rm -f $(TARGETS) *.txt
# rm (Remove) : 리눅스에서 파일을 삭제하는 명령어
# -f (Force) : 삭제할 파일이 없어도 에러를 띄우지 말고 강제로 진행.
# 빌드된 파일이 없는 상태로 make clean 을 입력해도 정리한다. => 찌꺼기 정리 가능
# 지울 파일들 : TARGETS, *.txt
# *.txt : 프로그램을 실행하면 생성되는 로그파일(ex) log.txt)까지 한꺼번에 지워서 폴더를 초기상태로 만듦. 

# 실행 테스트
test: all
	@echo "빌드 완료. 터미널에서 실행하기."
	@echo "1.  ./master  (감시)"
	@echo "2.  ./generator  (정상데이터 송신)"
	@echo "3.  ./attacker  (비트 단위 데이터 변조 공격)"

#test: all(의존성) : test를 실행하기 전에 all 명령을 먼저 수행하라는 뜻.
# all을 수행한 뒤 최신파일 상태에서 test가 진행된다.
# @ (At Sign) : 명령어 앞에 @를 붙이면 
# 터미널에 명령어는(echo "") 출력하지 않고 그 결과 값만 출력한다. 