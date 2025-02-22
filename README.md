# WEBSOCKETTEST

/topic/request
요청(request) 관련 로그 데이터
메서드, URL, 헤더, 바디, 클라이언트 IP 등의 정보 포함
/topic/response
응답(response) 관련 로그 데이터
상태 코드, 헤더, 응답 바디, 처리 시간 등의 정보 포함
/topic/transaction
트랜잭션 처리 관련 로그 데이터
전체 처리 시간, 성공/실패 여부 등의 정보 포함
/topic/process
프로세스(함수 호출) 추적 관련 로그 데이터
함수 이름, 클래스 이름, 파라미터, 실행 시간 등의 정보 포함
5. /topic/metrics
시스템 메트릭스 데이터
CPU, 메모리, 디스크, 네트워크 사용량 등의 정보 포함
/topic/queue_status
큐 상태 모니터링 데이터
큐 크기, 타임스탬프 등의 정보 포함
7. /topic/tps
TPS(Transaction Per Second) 측정 데이터
초당 트랜잭션 수와 타임스탬프 정보 포함