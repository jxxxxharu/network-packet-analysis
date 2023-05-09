import pyshark

# Create a capture object and set the interface to capture on
capture = pyshark.LiveCapture(display_filter='QUIC')

# Start the capture
capture.sniff(timeout=1)

for packet in capture:
    print(packet)
