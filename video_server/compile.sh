# 동영상 파일을 DASH 형식으로 변환
ffmpeg -i videos/video02.mp4 -c:v libx264 -b:v 1M -c:a aac -b:a 128k -vf "scale=-1:720" -f dash -min_seg_duration 5000 dash/dash.mpd

# 동영상 파일을 HLS 형식으로 변환
ffmpeg -i videos/video02.mp4 -profile:v baseline -level 3.0 -s 640x480 -start_number 0 -hls_time 10 -hls_list_size 0 -f hls hls/hls.m3u8
