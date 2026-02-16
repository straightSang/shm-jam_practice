import numpy as np
from scipy import signal as sp_signal
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider

#1. 기본값 및 파라미터
fs = 1000
t = np.linspace(0, 1, fs, endpoint=False)
cutoff = 50.0 #초기 컷오프 값
noise_str = 0.2 #가우시안 잡음 강도
is_paused = False

#2. 그래프 레이아웃 설정

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10)) #도화지, 2행1열로 쪼개기

#3. 시간 영역 (BPSK 복원 확인용)
line_mixed, = ax1.plot(t, np.zeros(fs), label="pure+jamming", alpha=0.6) #수신 신호
line_recovered, = ax1.plot(t, np.zeros(fs), label="recovered BPSK", color = 'red') #BPSK복원 신호
ax1.set_ylim(-3, 3)
ax1.set_title("BPSK signal recovery")
ax1.legend(loc='upper right')

#4. 주파수 영역 (fft)
freqs = np.fft.rfftfreq(fs, 1/fs) #x축 설정
line_fft, = ax2.plot(freqs, np.zeros(len(freqs)), color='green', label='Signal PSD') #fft 그래프: 재밍탐지 가능
line_threshold, = ax2.plot(freqs, np.zeros(len(freqs)), 'r--', alpha=0.4, label='Dynamic Threshold') #동적 임계치
ax2.legend(loc='upper right')
ax2.set_ylim(0, 1.2) #원래 수신하려고 한 신호: 1v 로 정규화.
ax2.set_xlim(0, 100) #원래 수신하려고 한 신호의 주파수: 10Hz
#fft.rfftfreq(fs, 1/fs) 에서 나오는 범위: 0Hz~fs/2Hz => 0~500Hz
ax2.set_title("Frequency: Peak & Dynamic Threshold")
ax2.legend(loc='upper right')

plt.tight_layout()

#5. 슬라이더: 컷오프 기준 조절 슬라이더
plt.subplots_adjust(bottom=0.2) #도화지 위치 조정, 슬라이더 위치
cutoff_slider = plt.axes([0.2, 0.05, 0.6, 0.03])
slider = Slider(cutoff_slider, 'LPF cutoff', 1.0, 150.0, valinit=cutoff)
#슬라이더 크기,위치, 범위최소/최대, 슬라이더가 초기에 가리키고 있을 값

#6. 데이터를 BPSK 신호로 변환
def generate_BPSK(fs, t, carrier_freq=10): #샘플수, 시간축, 주파수
    """
    실전에서의 전송할 데이터의 비트 수 & 이진 변환 방법은?
    """
    bits_num = 10 #변환할 데이터의 총 비트 수
    bits = np.random.randint(0, 2, bits_num) #리스트반환 #0~(2-1) 범위의 숫자를 랜덤으로 bits_num개 생성
    # 비트 0 -> 사인파 +1, 비트 1-> 사인파 -1 / 비트 시간 늘리지 (항재밍성 증가)
    bit_signal = np.repeat(bits * (-2) + 1, fs//bits_num)
    return bit_signal * np.sin(2*np.pi*carrier_freq*t), bits

#7. 신호생성 및 필터링    
def update(frame):
    if is_paused:return line_mixed, line_recovered, line_fft, line_threshold
    #1. 신호생성
    #정상신호
    clean_signal, bits = generate_BPSK(fs, t)
    #재밍신호 (주기적 발생)
    jamming_ampl = 0.8 if(frame//20) % 2 ==0 else 0
    jamming = jamming_ampl * np.sin(2*np.pi*20*t) #재밍 20Hz
    #노이즈 (AWGN)
    noise = np.random.normal(0, noise_str, fs)
    mixed = clean_signal + jamming + noise

    #2. fft 및 피크탐지
    fft_val = np.abs(np.fft.rfft(mixed)) / (fs/2) #rfft는 양수 방향만 남김(절반), 샘플링으로 인해 배가 된 신호 원상복귀위해 나눔.
    max_ind = np.argmax(fft_val) #평균보다 강도가 지나치게 큰 주파수(피크)의 인덱스
    peak_freq = freqs[max_ind]  #그 주파수(x축)
    peak_magn = fft_val[max_ind] #그 주파수의 세기(y축)
    
    #3. 동적 임계치 계산
    #실시간 평균 잡음 레벨보다 주파수의 세기가 3배(안전계수배) 이상 튀어오르면 재밍일 확률이 높음
    avg_noise = np.mean(fft_val) #전체 주파수 세기의 평균: 잡음이 커지면 동적임계치도 커짐.
    dynamic_lim = avg_noise * 3.0 #안전계수 (3배) 곱하기
    threshold_data = np.full(len(freqs), dynamic_lim) #np.full(shape, contents)

    #4. 필터링 시스템: BSF(Notch) 로 재밍 제거, LPF(Butter)로 노이즈(고주파잡음) 제거
    #주의: 필터는 정상신호도 깎는다: 진폭왜곡, 위상왜곡. 필터 전후 SNR, BER 필요.
    #BSF(Notch) 필터: 피크>동적임계치 이고 재밍 주파수 대역이라면 재밍이라고 전제. 제거
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

    #LPF(Butter) 필터: slider로 기준주파수 정한 뒤 그 이상 주파수(고주파 잡음) 제거
    bl, al = sp_signal.butter(4, slider.val, btype='low', fs=fs) 
    #버터워스 필터: 차수(반복필터링), 기준주파수, 타입(LPF/HPF), 샘플링개수 
    fin_signal = sp_signal.lfilter(bl, al, filtered)


    #5. 그래프 선 데이터 업데이트: 필터링 이후 데이터 업데이트 필수
    #ax1, 주파수그래프
    line_mixed.set_ydata(mixed)
    line_recovered.set_ydata(fin_signal)
    #ax2, fft그래프
    line_fft.set_ydata(fft_val)
    line_threshold.set_ydata(threshold_data)

    return line_mixed, line_recovered, line_fft, line_threshold

#8. 애니메이션
ani = FuncAnimation(fig, update, interval=50, blit=False)
plt.show()








