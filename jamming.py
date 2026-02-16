import numpy as np
from scipy import signal as sp_signal
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button

#1. 기본값 및 파라미터_________
fs = 1000
t = np.linspace(0, 1, fs, endpoint=False)
jump_freqs = [50, 100, 150, 200] # 주파수 도약
cutoff = 50.0 #초기 컷오프 값
noise_str = 0.2 #가우시안 잡음(AWGN) 강도
is_paused = False
current_mode = "BPSK"
jamming_mode = 0 # 0: CW, 1: Barrage, 2: Sweep

#2. 그래프 레이아웃 설정________

fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 12)) #도화지, 2행1열로 쪼개기

#1). 시간 영역 (복원 확인용)
line_mixed, = ax1.plot(t, np.zeros(fs), label="pure+jamming", alpha=0.6) #수신 신호
line_recovered, = ax1.plot(t, np.zeros(fs), label="recovered signal", color = 'red') #BPSK복원 신호
ax1.set_ylim(-3, 3)
ax1.set_title("signal recovery")
ax1.legend(loc='upper right')

#2). 주파수 영역 (fft): 실시간 피크탐지 및 동적 임계치
freqs = np.fft.rfftfreq(fs, 1/fs) #x축 설정
line_fft, = ax2.plot(freqs, np.zeros(len(freqs)), color='green', label='Signal PSD') #fft 그래프: 재밍탐지 가능
line_threshold, = ax2.plot(freqs, np.zeros(len(freqs)), 'r--', alpha=0.4, label='Dynamic Threshold') #동적 임계치
ax2.legend(loc='upper right')

ax2.set_ylim(0, 1.5) #원래 수신하려고 한 신호: 1v 로 정규화.
ax2.set_xlim(0, 120) #원래 수신하려고 한 신호의 주파수: 10Hz
#fft.rfftfreq(fs, 1/fs) 에서 나오는 범위: 0Hz~fs/2Hz => 0~500Hz
ax2.set_title("Frequency: Peak & Dynamic Threshold")
ax2.legend(loc='upper right')

#3). 스펙트로그램: 공격패턴 기록
#100개 프레임 데이터를 저장할 버퍼
#imshow는 입력되는 데이터의 최댓값과 최솟값을 기준으로 색상을 정합니다. 
# 현재 FFT 값들이 너무 작으면(예: 0.1 이하), 전체 범위에서 0에 가까운 보라색으로만 보일 수 있습니다.
#해결책: 색상의 기준점(vmax)을 강제로 잡아주세요.
spec_buffer = np.zeros((100, len(freqs)))
img_spec = ax3.imshow(spec_buffer, aspect='auto', extent=[0, 120, 100, 0], cmap='viridis', vmin=0, vmax=1.0)
ax3.set_title("Spectrogram: Jamming Chart")
ax3.legend(loc='upper right')
ax3.set_ylabel("Time(frames)")
ax3.set_xlabel("Frequency(Hz)")

#4). 매칭필터& 실시간 BER 덱스트 표시
line_match, = ax4.plot(t, np.zeros(fs), color='red', label='Match filter')
ax4.set_ylim(-3, 3)
ax4.set_title("Match Filter")
ax4.legend(loc='upper right')

plt.tight_layout()



#3. 인터랙티브 기능

#1). 슬라이더: 컷오프 기준 조절 슬라이더
plt.subplots_adjust(bottom=0.2) #도화지 위치 조정, 슬라이더 위치

cutoff_slider = plt.axes([0.2, 0.12, 0.6, 0.03]) #0.2~0.4 #0.07~0.09
slider = Slider(cutoff_slider, 'LPF cutoff', 1.0, 150.0, valinit=cutoff)
#슬라이더 크기,위치, 범위최소/최대, 슬라이더가 초기에 가리키고 있을 값

#2). 버튼

signal_button = plt.axes([0.2, 0.05, 0.25, 0.04]) #0.5~0.7 #0.01~0.03
signal_mode = Button(signal_button, "Switching signal Mode")
jamming_button = plt.axes([0.55, 0.05, 0.25, 0.04]) #0.8~1.0 #0.04~0.06
btn_mode = Button(jamming_button, 'Switching Jamming Mode')

def signal_switching(event):
    global current_mode
    current_mode ="LFM" if current_mode=="BPSK" else "BPSK"
signal_mode.on_clicked(signal_switching)

def jamming_switching(event):
    global jamming_mode
    jamming_mode = (jamming_mode+1)%3
    mode = ["CW", "Barrege", "Sweep"]
    print("재밍 모드 변경{mode[jamming_mode]}")

btn_mode.on_clicked(jamming_switching)



#4. 핵심 로직 함수

#1). 데이터를 BPSK 신호로 변환
def generate_SIGNAL(frame):
    """
    실전에서의 전송할 데이터의 비트 수 & 이진 변환 방법은?
    """
    # 20프레임마다 주파수 도약
    jump_ind = (frame // 20) % len(jump_freqs)
    carry_freqs = jump_freqs[jump_ind]


    if current_mode == "BPSK":
        bits_num = 10 #변환할 데이터의 총 비트 수
        bits = np.random.randint(0, 2, bits_num) #리스트반환 #0~(2-1) 범위의 숫자를 랜덤으로 bits_num개 생성
        # 비트 0 -> 사인파 +1, 비트 1-> 사인파 -1 / 비트 시간 늘리지 (항재밍성 증가)
        bit_signal = np.repeat(bits * (-2) + 1, fs//bits_num)
        return bit_signal * np.sin(2*np.pi*carry_freqs*t), carry_freqs  # 정규화: -1 < sin < 1
    
    else: #LFM (Chirp)
        #frame에 따라 발사 타이밍 조정
        chirp = sp_signal.chirp(t, f0=carry_freqs-20, f1=carry_freqs+20, t1=1, method='linear')
        return chirp, carry_freqs


#2). 신호생성 및 필터링    
def update(frame):
    if is_paused:return line_mixed, line_recovered, line_fft, line_threshold, line_match
    #[1]. 신호생성
    # 정상신호
    clean_signal, carry_freqs = generate_SIGNAL(frame)

    # 재밍신호 (주기적 발생)
    if jamming_mode == 0: # CW
        jamming = 1.2 * np.sin(2*np.pi*20*t) #재밍 20Hz

    elif jamming_mode == 1: # Barrage
        noise_jamming = np.random.normal(0, 1.5, fs) #진폭이 1보다 크면 원래 신호도 많이 흔들린다. 
        b_b, a_b = sp_signal.butter(4, [10, 40], btype='bandpass',fs=fs) #10~40Hz 사이에 흩뿌려지는 노이즈.
        jamming = sp_signal.lfilter(b_b, a_b, noise_jamming)

    else: # Sweep: 신호들 사이를 왕복함
        f_sweep = 150 + (frame % 50) * 2 # 공격할 주파수 대역: 프레임 번호에 따라서 달라짐 150~248
        jamming = 1.2 * np.sin(2 * np.pi * f_sweep*t)

    # 노이즈 (AWGN)
    noise = np.random.normal(0, noise_str, fs)
    mixed = clean_signal + jamming + noise


    #[2] fft 및 피크탐지
    fft_val = np.abs(np.fft.rfft(mixed)) / (fs/2) # 정규화. 원신호의 진폭은 1V 가 되게 함.
    #rfft는 양수 방향만 남김(절반), 샘플링으로 인해 배가 된 신호 원상복귀위해 나눔.
    max_ind = np.argmax(fft_val) #평균보다 강도가 지나치게 큰 주파수(피크)의 인덱스
    peak_freq = freqs[max_ind]  #그 주파수(x축)
    peak_magn = fft_val[max_ind] #그 주파수의 세기(y축)
    
    #[3] 동적 임계치 계산
    #실시간 평균 잡음 레벨보다 주파수의 세기가 3배(안전계수배) 이상 튀어오르면 재밍일 확률이 높음
    avg_noise = np.mean(fft_val) #전체 주파수 세기의 평균: 잡음이 커지면 동적임계치도 커짐.
    dynamic_lim = avg_noise * 3.0 #안전계수 (3배) 곱하기
    threshold_data = np.full(len(freqs), dynamic_lim) #np.full(shape, contents)


    #[4] 필터링 시스템: BSF(Notch) 로 재밍 제거, LPF(Butter)로 노이즈(고주파잡음) 제거
    # 적응형 방어방식 필요(동적 대응)
#____________________수정필요. 현재 방어 개허접함

    #1. Notch
    if peak_magn > dynamic_lim and not(carry_freqs-10 < peak_freq < carry_freqs+10):
        #피크의 주파수를 실시간으로 추적한 뒤 내 신호의 대역이 아닐 때만 Notch 필터 적용
        bn, an = sp_signal.iirnotch(peak_freq, 30.0, fs=fs) #제거주파수, 품질계수, 샘플수
        notched = sp_signal.lfilter(bn, an, mixed)
        ax2.set_facecolor('mistyrose')
    else:
        notched = mixed
        ax2.set_facecolor('white')
    """
    #주의: 필터는 정상신호도 깎는다: 진폭왜곡, 위상왜곡. 필터 전후 SNR, BER 필요.
    #1. BSF(Notch) 필터: 피크>동적임계치 이고 재밍 주파수 대역이라면 재밍이라고 전제. 제거
    if peak_magn > dynamic_lim and 18 < peak_freq < 22: #교란탐지
        #피크가 임계치를 넘었을 때만 Notch 필터 가동. 신호왜곡 최소화: 노이즈 증폭 방지 및 효율 증가
        bn, an = sp_signal.iirnotch(peak_freq, 30.0, fs=fs) # lfilter에 들어갈 계수를 반환함
        #제거하려는 주파수(중심주파수), 품질계수(중심주파수/대역폭), 샘플링개수
        #대역폭 조절방법: 필터 차수 높이기, Q값 조절, 
        filtered = sp_signal.lfilter(bn, an, mixed) #중심 주파수를 제거한 신호를 반환
        ax2.set_facecolor('mistyrose')

    else:
        filtered = mixed
        ax2.set_facecolor('white')
"""
    #2. LPF(Butter) 필터: slider로 기준주파수 정한 뒤 그 이상 주파수(고주파 잡음) 제거
    bl, al = sp_signal.butter(4, slider.val, btype='low', fs=fs) 
    #버터워스: 차수(반복필터링), 기준주파수, 타입(LPF/HPF), 샘플링개수 
    recovered = sp_signal.lfilter(bl, al, notched)


    #3. 매칭필터 적용: 상관관계 구하기
    # # 송신 반송파와 곱하여 위상 성분 추출
    if current_mode=="BPSK":
        template = np.sin(2 * np.pi * carry_freqs * t)
        raw_matched = recovered * template  # 수신신호*송신신호 : BPSK 상관관계 구하기
        matched = np.zeros_like(raw_matched) #인자와 똑같은 타입, 형태의 0으로 채워진 변수만들기.

        #적분하기: 비트별 계단모양 / 각 계단의 높이로 신뢰도&재밍정도 알 수 있음.
        bits_num = 10 # 1초당 비트 수
        sample_bit = fs//bits_num #비트 하나당 할당되는 샘플수
        #1번 비트: 0번~99번 샘플, 2번비트: 100번~199번 비트 ...
        for i in range(bits_num):
            start = i * sample_bit # 0, 100, 200,..
            end = (i+1)*sample_bit #인덱스 역할 # 100, 200,... 

            #이산 그래프에서는 평균 == 적분임.
            bits_avg = np.mean(raw_matched[start:end]) #단일 실수 반환
            matched[start:end] = bits_avg # 100개의 요소를 전부 같은 수(한 비트를 나타내는 샘플 100개의 평균)로 채움.


        """
        # --- 추가: 비트별로 에너지를 뭉쳐서 보여주기 (시각화 개선) ---
        bits_num = 10
        samples_per_bit = fs // bits_num
        matched = np.zeros_like(raw_matched)
        
        for i in range(bits_num):
            start, end = i * samples_per_bit, (i + 1) * samples_per_bit
            # 한 비트 구간의 평균값을 구해서 해당 구간을 채움
            avg_val = np.mean(raw_matched[start:end])
            matched[start:end] = avg_val
            """

    else:
        template = sp_signal.chirp(t, f0=carry_freqs-20, f1=carry_freqs+20, t1=1, method='linear') #template=송신신호
        correlation = sp_signal.correlate(recovered, template, mode='same')  # corelate : LFM 상관관계 구하기
        matched = np.abs(correlation) / max(np.abs(correlation)) # 정규화

    # BPSK는 수신신호 비트가 0이면 fin_filtered=+1, 1이면 -1
    # LFM은 처리 더 해야 함.



    #[5] 스펙트로그램 업데이트
    global spec_buffer
    spec_buffer = np.roll(spec_buffer, 1, axis=0) #한 행씩 밑으로 밀어내기
    spec_buffer[0, :] = fft_val # fft 그래프 한 개 = 한 행
    #ax3
    img_spec.set_data(spec_buffer)


    #[6] 그래프 선 데이터 업데이트: 필터링 이후 데이터 업데이트 필수
    #ax1, 주파수그래프+notch&LPF
    line_mixed.set_ydata(mixed)
    line_recovered.set_ydata(recovered)
    #ax2, fft그래프
    line_fft.set_ydata(fft_val)
    line_threshold.set_ydata(threshold_data)
    #ax4, match+notch&LPF 주파수 필터그래프
    line_match.set_ydata(matched)

    return line_mixed, line_recovered, line_fft, line_threshold, line_match

#5. 애니메이션
ani = FuncAnimation(fig, update, frame=30, interval=50, blit=False)
""" blit: True로 설정하면 변경된 부분만 다시 그려 성능이 향상되지만, 
update 함수가 반복 가능한(iterable) 아티스트 객체를 반환해야 함
interval: 프레임 사이의 지연 시간
"""
# plt.show()
ani.save('anim.gif', writer='pillow', fps=20)
#writer: 비디오 인코딩 라이브러리 / ffmpeg, imageMagick
# fps: 재생 속도