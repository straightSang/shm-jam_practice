https://www.notion.so/BPSK-2f4b6434b78a81f68755ccfea6e014a6?source=copy_link


### 1. Multi-threasded Real-time Jamming Detection System

- 배경: 고출력 재밍 신호로부터 군 위성통신 가용성을 확보하기 위한 실시간 탐지 및 대응 기술 필요
- 목적: 대량의 수신 신호 데이터를 지연없이 처리하고, 디지털 필터링을 통해 통신 품질을 복원하는 아키텍쳐 구현

- ### 2, 시스템 아키텍쳐

- 프로세스 구조:
    - (DAQ)Data Aquisituion Module: 위성 수신 신호 데이터 시뮬레이션 및 버퍼 적재 (수신기)
    
    [BPSK/QPSK, QAM/LFM](https://www.notion.so/BPSK-QPSK-QAM-LFM-2fbb6434b78a8069b61fc4ab28809184?pvs=21)
    
    [DAQ](https://www.notion.so/DAQ-2fab6434b78a809ab870d54216e70d0f?pvs=21)
    
    - Signal Processing Module: FFT분석, LC 필터 기반 디지털 필터링(Consumer) (필터, 분석)
    - Detection & Alert Module: 임계치 기반 재밍 판단 및 이벤트 발생 (Controller) (판단, CPU)
- 통신 방식: 프로세스 간 공유메모리(Shared Memory) 및 Queue를 활용한 고속 데이터 전송

### 3. 주요 기능 세부 설계 (Functional Design)

- 신호 모델링: BPSK/QPSK 위상 변조 신호 및 AWGN(가우시안 잡음) 생성

[신호모델링(BPSK/QPSK 변조신호)](https://www.notion.so/BPSK-QPSK-2fab6434b78a80ffb1d1d1fa8f80343e?pvs=21)

- 재밍 모델링: 단일 주파수(CW) 및 광대역(Barrage) 재밍 시나리오 구현

- 디지털 필터 설계(LC 필터 원리 적용)
    - 신호 복원을 위한 Low Pass Filter 설계
    - 재밍 대역 제거를 위한 Notch Filter 설계 (Butterworth 방식)
    
    [Notch 필터](https://www.notion.so/Notch-2fab6434b78a80478e49d3e3dea5f0a5?pvs=21)
    
- 실시간 탐지 알고리즘
    - FFT 기반 Power Spectral Dentisty (PSD) 계산
    - Dynamic Threshold(동적 임계치 기반 이상 신호 탐지 로직)
    
    [동적임계치(Dynamic Threshold)](https://www.notion.so/Dynamic-Threshold-2fab6434b78a809c9850ccd8d72c6142?pvs=21)

  ### 3-2. 필요한 것

- 신호 생성 및 수집
    - 수신신호 생성
    - 재밍신호 생성
    - 신호 복원 필터 알고리즘
    - 재밍 탐지 및 제거 필터 알고리즘
- FFT 함수 구현 및 LC기반필터 알고리즘 구현
- 임계치 설정
- 임계치 기반 재밍 탐지 알고리즘
- 이벤트 발생?

### 4. 실시간성 확보 방안 (Real-time Strategy)

- 병렬 처리: python multipeocessing 을 활용한 CPU 코어별 역할 분담
- 지연 최소화: 데이터 처리 단위(chunk size) 최적화를 통한 입출력 레이턴시 제어
- 최적화: Numpy 벡터 연산을 활용하여 반복문 제거 및 연산 속도 극대화

### 5. 검증 및 평가 방안

- 정확도: 재밍 신호 유무에 따른 탐지율(Detection rate) 및 오보율(Flase Alarm rate) 측정
- 성능: 초당 처리 샘플 수 및 프로세스별 CPU/메모리 점유율 모니터링
- 가시성: 실시간 스펙트로그램 시각화를 통한 탐지 결과 확인
- 
    
    | **항목** | **현황** | **상세 내용** |
    | --- | --- | --- |
    | **신호 모델링 (BPSK/QPSK)** | **미완료** | 현재는 단순한 사인파(`sin`)를 씁니다. 실제 위성 통신에 쓰이는 위상 변조(BPSK 등) 신호 생성 로직이 필요합니다. |
    | **재밍 모델링 (CW/Barrage)** | **부분 완료** | 단일 주파수(CW) 재밍(20Hz)은 구현했습니다. 다만, 전 대역을 덮어버리는 광대역(Barrage) 재밍은 아직입니다. |
    | **디지털 필터 (Low Pass)** | **완료** | 슬라이더로 조절 가능한 LPF가 구현되어 있습니다. |
    | **디지털 필터 (Notch Filter)** | **완료** | 특정 주파수만 쏙 빼내는 Notch Filter 설계. |
    | **실시간 탐지 (PSD)** | **완료** | FFT를 통해 에너지 밀도를 확인하는 로직이 구현되어 있습니다. |
    | **Dynamic Threshold** | **완료** | 현재는 고정된 값(0.5 등)을 기준으로 판단합니다. 잡음 세기에 따라 기준값이 변하는 '동적 임계치' 로직이 필요합니다. |
    | AWGN |  |  |
    | J/S Ratio |  |  |
    | 스펙트로그램 |  |  |
    | 링크버짓 |  |  |
| **항목** | **현황** | **상세 내용** |
| --- | --- | --- |
|  **① J/S Ratio (Jamming-to-Signal Ratio)** | **미완료** | 재밍 신호가 원신호보다 얼마나 강한지 나타내는 비율.
• **공식:** $J/S = 10 \log_{10}(P_j / P_s) \text{ [dB]}$
• 실시간 J/S 비율을 계산. 이 값이 커질수록 통신 불가능. |
| **② 링크버짓 (Link Budget)** | **미완료** | 위성에서 보낸 신호가 수신기에 도달할 때까지 발생하는 이득과 손실의 총합.
• **적용:** 단순히 신호를 만드는 게 아니라, 거리 손실(Path Loss) 등을 계산하여 최종 수신단에 도달할 신호의 전력($P_r$)을 결정하는 기준점임. |
| **③ 스펙트로그램 (Spectrogram)** | **완료** | FFT는 순간의 주파수만 나타냄. **스펙트로그램**은 시간에 따라 주파수가 어떻게 변했는지 세로축(시간), 가로축(주파수), 색상(강도)의 3차원 지도로 보여줌. |
| LFM | **완료** |  |
| event 버튼 | **완료** |  |
| 주파수 도약 | 완료 |  |
| 매칭 필터 | 완료 |  |
| BER | 미완료 |  |

