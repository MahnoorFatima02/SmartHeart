# Smart Heart

## Setup 
Clone the git repository using this link:  MahnoorFatima02/SmartHeart.git


## Smart Heart
Smart Heart is a efficient non-invasive heart rate measuring device. The primary goal of this project is to create a comprehensive heart rate detection and analysis system. It includes developing a real-time heart rate detection algorithm to calculate heart rate variability (HRV) and integrating with Kubios Cloud service for in-depth HRV analysis. It can also display stress and recovery metrics on the device to provide users with real-time feedback on their physiological health.

Below images illustrate our project's display:

<p>
<img src="https://github.com/MahnoorFatima02/SmartHeart/blob/main/Screenshots/Heart%20Rate.png" alt="heart rate" width="350" height="180" /> &nbsp;&nbsp;
<img src="https://github.com/MahnoorFatima02/SmartHeart/blob/main/Screenshots/Options.png" alt="options page" width="350" height="180" /> &nbsp;&nbsp;
<img src="https://github.com/MahnoorFatima02/SmartHeart/blob/main/Screenshots/Ready.png" alt="ready page" width="350" height="180" /> &nbsp;&nbsp;
<img src="https://github.com/MahnoorFatima02/SmartHeart/blob/main/Screenshots/Kubios.png" alt="kubios page" width="350" height="180" /> &nbsp;&nbsp;
<img src="https://github.com/MahnoorFatima02/SmartHeart/blob/main/Screenshots/History.png" alt="history page" width="350" height="180" /> &nbsp;&nbsp;
<img src="https://github.com/MahnoorFatima02/SmartHeart/blob/main/Screenshots/History%20measurement.png" alt="history measurement page" width="350" height="180" /> &nbsp;&nbsp;
  
</p>

## Description
Heart rate is cardiac muscle contractions per minute. It is recorded in bpm (beats per minute). Heart rate in human beings ranges from 40 bpm to 200 bpm, nonetheless, higher values are recorded in athletes. HRV is the fluctuations in the time intervals amidst each heartbeat. A healthy adult has an average HRV of 42 milliseconds, with a normal range from 19 to 75 milliseconds. 

The HRV is regulated by a core part of the nervous system called the Autonomic Nervous System (ANS). The ANS delivers signals to the hypothalamus, which aligns the body either to react actively or to relax various body functions altering HRV. 

In the project, photoplethysmography (PPG) is used to measure the heart rate by generating a pulsatile waveform. PPG is a valuable tool, offering a non-invasive surface level optical approach to determine HRV. It uses optics to measure the blood circulation changes in the capillaries of the body. A thin skin surface that is enriched with blood capillaries is exposed to light by a light-emitting diode (LED) which can be either an infra-red rays or red LED.
The light reflected by the skin tissues is captured by a photodiode depicting the blood volume changes. The project uses Crowtail Pulse sensor v2.0 by placing it on the same side as the light source to capture the reflected light intensity. It is recommended to place the sensor at the earlobe, wrist or finger for accurate readings.


The intensity of the light is converted into a voltage signal by photodiode. The amplitude of the signal depends on the light absorbed by the blood capillaries, the absorbing power is directly proportional to the flow of blood cells through the tissues. Heart rate corresponds to the periodicity of this PPG signal, which can be used towards estimating HRV. In the project, the PPG signal is processed in time-domain; the peaks are determined by an advanced algorithm, providing live heart rate value and pulse signal. Heart rate is the peak to peak interval of the signal and by further processing it, the device displays advanced heart rate metrics.


## System

The project is a sophisticated amalgamation of its hardware and software components required for an accurate heart rate monitoring system. 

Below image illustrates our project's system: 

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <img src="https://github.com/MahnoorFatima02/SmartHeart/blob/main/Screenshots/System.png" alt="system logic" width="750" height="380" />

The core of the system is its PPG sensor (Crowtail Pulse sensor v2.0) that is strategically positioned on the user’s skin to detect the reflected light. The sensor is connected to Raspberry pico through an ADC pin (ADC_0), it interfaces with an electric diode to form the basis of signal acquisition.

The signal processing unit performs advanced algorithms aimed to calculate heart rate from the captured PPG signals. The system incorporates a user interface with the help of rotary encoder. The I2C interface on the Pico board interacts with the OLED display to show the heart rate on the OLED screen and a live pulse of a fluctuating heart rate signal as well as other options like Kubios and MQTT.

To increase system versatility, pico board is equipped with the required libraries for WLAN connectivity. The Pico board establishes a TCP/IP socket connection with the Kubios server using WLAN connection. The real time heart rate data is sent to Kubios software, a crucial element in deep analysis of heart rate. Additionally, MQTT protocol connection with LAN facilitates fluid data communication between client laptops and the system. 


## Algorithm Implementation 

The project was a noble endeavour in regard that it aimed to improve human well-being by monitoring heart rates in real time. It encourages people to take proactive health measures and sustain their fitness levels.

Below image illustrates our project's logic:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <img src="https://github.com/MahnoorFatima02/SmartHeart/blob/main/Screenshots/Flow%20Chart.png" alt="logic" width="750" height="380" />

For further information, please see the [documentation]( https://github.com/MahnoorFatima02/SmartHeart/blob/main/smart-heart-documentation.pdf)


## Roadmap
For future developments, there are ideas to implement an algorithm that assesses the user’s emotions based on HRV. This feature would be a useful addition to our device because it can be utilised in the healthcare field where there is a need to understand a patient’s emotions without intruding on the patient.


## Authors and acknowledgment
My colleagues Nhi Dinh and Trung Vu. 

