# video-blocker

진행 과정은 다음과 같다. 모든 실습은 Ubuntu 20.04 환경에서 진행되었다.

1. [동영상 스트리밍 서버 구축](#1-동영상-스트리밍-서버-구축)
2. [DASH/HLS 패킷 분석](#2-dashhls-패킷-분석)
3. [DASH/HLS 패킷 필터링 프로그램](#3-dashhls-패킷-필터링-프로그램)

<br>

### 1. 동영상 스트리밍 서버 구축

---

DASH, HLS 프로토콜을 지원하는 간단한 동영상 스트리밍 서버를 구축하였다.

![DASH 프로토콜과 HLS 프로토콜을 위한 비디오 인코딩](https://github.com/jxxxxharu/network-packet-analysis/assets/80589294/6f49e9f9-df9f-47c2-bab9-56d0ed1a9571)

사실 프로젝트 초반에는 패킷 분석을 통해 네트워크 트래픽에서 DASH, HLS 프로토콜을 식별할 만한 매직 헤더를 통해 찾을 것으로 기대했으나, 패킷 헤더에는 특별한 시그니처가 나타나지 않았다. 따라서 페이로드 분석이 요구되었다. DASH, HLS는 HTTP 기반이므로 HTTP 패킷을 확인해야 했는데, 대부분의 동영상 서비스가 HTTPS를 사용하는 상황에서 보안상 페이로드는 확인이 어려워 Wireshark를 통한 패킷 모니터링이 제한되었다. 결과적으로 직접 DASH/HLS 기반의 간단한 스트리밍 서비스를 구축하게 되었다.

스트리밍할 영상은 각 프로토콜에 알맞게 인코딩 되어야 하며, 이를 위해 `FFmpeg`를 사용하였다.
`FFmpeg`는 멀티미디어 디코딩, 인코딩에 대한 기능을 제공하는 오픈 소스 라이브러리다.

```bash
$ ffmpeg -i videos/video02.mp4 -c:v libx264 -b:v 1M -c:a aac -b:a 128k -vf "scale=-1:720" -f dash -min_seg_duration 5000 dash/dash.mpd # DASH
```

```bash
$ ffmpeg -i videos/video02.mp4 -profile:v baseline -level 3.0 -s 640x480 -start_number 0 -hls_time 10 -hls_list_size 0 -f hls hls/hls.m3u8 # HLS
```

<br>

`video_server/app.py`

0. `/` 경로 접속 --> `index.html` 템플릿 --> `video` 디렉토리 내의 `.mp4` 파일 전송
1. `/dash` 경로 접속 --> `dash.html` 템플릿 --> `dash` 디렉토리 내의 `.mpd` 파일 전송
2. `/hls` 경로 접속 --> `hls.html` 템플릿 --> `hls` 디렉토리 내의 `.m3u8` 파일 전송

<br>

### 2. DASH/HLS 패킷 분석

---

Wireshark를 통해 위에서 구현한 동영상 서버의 동작 시 나타나는 DASH/HLS 패킷 및 관련 트래픽을 분석하였다.

- **DASH 패킷**
  <br>`http.request.uri contains ".m4s" or http.request.uri contains ".mpd"`

  1.  TCP 연결
      <br>클라이언트는 DASH 동영상을 요청하기 위해 우선 서버와 TCP 연결 (3-way handshake)을 설정한다.<br>TCP는 신뢰성 있는 연결 지향형 프로토콜로, 클라이언트와 서버 간에 신뢰성 있는 데이터 전송을 제공한다.
      ![TCP 연결](https://github.com/jxxxxharu/network-packet-analysis/assets/80589294/fb1cd431-059f-4348-a8d2-4ae5d10d0dcd)

  2.  HTTP 요청
      <br>TCP 연결이 설정되면 클라이언트는 서버에게 DASH 동영상에 대한 정보를 요청하는 HTTP GET 요청 메시지를 보낸다.
      ![HTTP 요청](https://github.com/jxxxxharu/network-packet-analysis/assets/80589294/6fa5d60d-e7ff-4352-9cbf-f3ac45947fac)

  3.  HTTP 응답
      <br>서버는 클라이언트 요청에 대한 HTTP 응답 메시지를 전송한다. 응답에는 DASH 동영상에 대한 메타데이터와 함께 DASH 매니페스트 파일(.mpd)이 포함된다.
      ![HTTP 응답 (1)](https://github.com/jxxxxharu/network-packet-analysis/assets/80589294/a771313f-392c-4c7e-a733-dfad65a52f24)

      <br>
      그런데 아래와 같이 200이 아닌 304가 뜨는 경우가 있다.

      ![HTTP 응답 (2)](https://github.com/jxxxxharu/network-packet-analysis/assets/80589294/91c7fb7d-b155-4721-a1ce-8f945ea97439)

      HTTP 상태 코드 304 (Not Modified)는 클라이언트가 이전에 요청한 리소스가 변경되지 않았음을 나타낸다. 처음 .mpd 파일을 요청 응답 할 때 브라우저 캐시에 해당 .mpd 파일이 남아있어서, 클라이언트가 동일한 .mpd 파일을 다시 요청할 경우 서버는 304 코드를 반환하며 실제 파일 데이터를 다시 전송하지 않는다고 한다.

  4.  DASH 세그먼트 요청
      <br>클라이언트는 매니페스트에 나열된 각 세그먼트에 대해 비디오 세그먼트 파일(.m4s)을 요청하는 HTTP GET 요청을 보낸다. 클라이언트는 필요한 세그먼트를 지속적으로 요청하여 전체 동영상을 받게 된다.

  5.  DASH 세그먼트 응답
      <br>서버는 클라이언트의 세그먼트 요청에 대해서 비디오 세그먼트 파일(.m4s)을 포함한 HTTP 응답을 전송한다.
      ![DASH 세그먼트 응답](https://github.com/jxxxxharu/network-packet-analysis/assets/80589294/a387f2ca-5f4d-441b-bcd4-a1a7ed8bd55b)

  6.  TCP 연결 해제
      <br>클라이언트와 서버의 단일 세그먼트의 요청과 응답이 완료되면 TCP는 종료 (4-way handshake) 된다.

<br>

- **HLS 패킷**
  <br>`http.request.uri contains ".ts" or http.request.uri contains ".m3u8"`

  HLS도 DASH 와 마찬가지로 'TCP 연결 --> HTTP 기반 세그먼트 요청/응답 --> TCP 연결 해제' 사이클을 동일하게 거친다.

  1.  TCP 연결
      <br>클라이언트는 HLS 동영상을 요청하기 위해 우선 서버와 TCP 연결 (3-way handshake)을 설정한다.
      ![TCP 연결](https://github.com/jxxxxharu/network-packet-analysis/assets/80589294/bad3719f-7d9b-40a2-8225-e596d6cb4cdf)

  2.  HTTP 요청
      <br>클라이언트는 TCP 연결을 통해 서버에게 HLS 동영상에 대한 정보를 요청하는 HTTP GET 요청 메시지를 보낸다.
      ![HTTP 요청](https://github.com/jxxxxharu/network-packet-analysis/assets/80589294/db229f2c-e318-4e48-baf8-f57605950568)

  3.  HTTP 응답
      <br>서버는 클라이언트 요청에 대한 HTTP 응답 메시지를 전송한다. 응답에는 HLS 동영상에 대한 메타데이터와 함께 DASH 매니페스트 파일(.m3u8)이 포함된다.
      ![HTTP 응답](https://github.com/jxxxxharu/network-packet-analysis/assets/80589294/d640946a-b141-435d-8012-aa96bdf744a2)

  4.  세그먼트 요청 (HTTP)
      <br>클라이언트는 매니페스트에 나열된 각 세그먼트에 대해 비디오 세그먼트 파일(.ts)을 요청하는 HTTP GET 요청을 보낸다. 클라이언트는 필요한 세그먼트를 지속적으로 요청하여 전체 동영상을 받게 된다.

  5.  DASH 세그먼트 응답 (HTTP)
      <br>서버는 클라이언트의 세그먼트 요청에 대해서 비디오 세그먼트 파일(.ts)을 포함한 HTTP 응답을 전송한다.
      ![DASH 세그먼트 응답](https://github.com/jxxxxharu/network-packet-analysis/assets/80589294/a19c93b9-d9b8-44da-b2e0-d4bd95f82564)

  6.  TCP 연결 해제
      <br>클라이언트와 서버의 단일 세그먼트의 요청과 응답이 완료되면 TCP는 종료 (4-way handshake) 된다.

<br>

### 3. DASH/HLS 패킷 필터링 프로그램

---

리눅스의 `iptables`는 패킷 필터링(Packet Filtering) 도구로, 방화벽 구성이나 NAT에 사용된다.

```
💡 NAT(Network Address Translation)
개인 네트워크의 여러 기기가 하나의 공인 IP 주소로 외부와 통신할 수 있게 하는 기술로,
사설 IP(Private IP)를 공인 IP(Public IP)로 변환하여 인터넷 연결을 가능하게 함.
```

<br>

```bash
$ sudo iptables -A INPUT -p tcp --dport 0:65535 -m --string string "GET /" --algo kmp -m string --string ".m3u8" --algo kmp -j DROP
$ sudo iptables -A INPUT -p tcp --dport 0:65535 -m --string string "GET /" --algo kmp -m string --string ".ts" --algo kmp -j DROP
$ sudo iptables -A INPUT -p tcp --dport 0:65535 -m --string string "GET /" --algo kmp -m string --string ".m4s" --algo kmp -j DROP
$ sudo iptables -A INPUT -p tcp --dport 0:65535 -m --string string "GET /" --algo kmp -m string --string ".mpd" --algo kmp -j DROP
```

<p float="left">
    <img src="https://github.com/jxxxxharu/network-packet-analysis/assets/80589294/2bb87628-5ef3-4169-b45c-eb49a30efc53" alt="실행 결과 (1)" style="width: 36%; margin-right: 20%;" />
    <img src="https://github.com/jxxxxharu/network-packet-analysis/assets/80589294/0c6d7ae2-090f-4491-b8d9-74cacee7c971" alt="실행 결과 (2)" style="width: 32%;" />
</p>

<br>

### 4. TCP Reset Attack

---

blah
