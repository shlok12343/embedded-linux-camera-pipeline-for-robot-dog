## Raspberry Pi Zero 2 W – Camera Development System Setup

This document defines the baseline system configuration and verification steps for using a **USB HD Camera 5MP 100° Microphone (Image Sensor OV5693)** on a **Raspberry Pi Zero 2 W** running embedded Linux. It is intended as internal technical documentation to standardize development environments, not as an end‑user tutorial.

---

## OS Assumptions

- **Hardware**
  - **Board**: Raspberry Pi Zero 2 W
  - **Camera**: USB UVC camera, 5 MP, 100° FOV, integrated microphone, OV5693 image sensor
  - **USB topology**: Camera connected to the Pi Zero 2 W via the USB **data** port (not the power‑only port); use an OTG adapter or powered USB hub as required.

- **Operating System**
  - **Base**: Raspberry Pi OS (Debian-based), Bookworm or newer
  - **Variant**: Lite/headless image is sufficient (no desktop required)
  - **Architecture**: 32-bit or 64-bit; kernel version **5.15+** or later recommended

- **Kernel / Driver Expectations**
  - `CONFIG_VIDEO_DEV` enabled
  - `CONFIG_USB_VIDEO_CLASS` enabled (module `uvcvideo`)
  - ALSA stack enabled (`snd_usb_audio` for the camera microphone)
  - `/dev/video*` nodes managed by `udev`

---

## Enabling the USB OV5693 Camera

The target camera is a **USB** device implementing the **USB Video Class (UVC)** and **USB Audio Class (UAC)** specifications. No dedicated Raspberry Pi firmware flags (e.g. `start_x`, legacy CSI camera enable, device tree overlays) are required beyond having a standard, up‑to‑date Raspberry Pi OS installation.

### Hardware and power constraints

- **USB host mode**
  - Use the micro‑USB port labeled `USB` (not `PWR`) on the Pi Zero 2 W.
  - Connect via a reliable OTG adapter; for multi‑device setups, use a powered USB hub.

- **Power**
  - Ensure the system has a stable 5 V supply; the Zero 2 W has limited USB power budget.
  - If camera enumeration is unreliable or disconnects under load, move to a powered hub.

### Kernel module expectations

The camera should be automatically bound by the `uvcvideo` driver, and the microphone by `snd_usb_audio`.

- **Expected modules**
  - `uvcvideo` – USB Video Class
  - `videodev` – Video4Linux2 core
  - `snd_usb_audio` – USB audio for microphone

No explicit configuration is required if these are built into the kernel, but they can be verified and loaded as modules if needed (see verification section).

---

## Required Packages

Install the following base set of packages for camera development, debugging, and pipeline work. Commands assume `apt` and appropriate privileges.

- **System information / USB utilities**
  - `usbutils` – provides `lsusb`
  - `pciutils` – not strictly required on Pi, but harmless and useful in some tooling

- **Video4Linux2 tooling**
  - `v4l-utils` – `v4l2-ctl`, `qv4l2`, etc. for inspecting and configuring V4L2 devices

- **Multimedia / pipeline tooling**
  - `ffmpeg` – quick capture, encode, and test of video/audio
  - `gstreamer1.0-tools` – `gst-launch-1.0` and related tools
  - `gstreamer1.0-libav` – FFmpeg codec bridge for GStreamer
  - `gstreamer1.0-plugins-base`
  - `gstreamer1.0-plugins-good`
  - `gstreamer1.0-plugins-bad`
  - `gstreamer1.0-plugins-ugly` – only if licenses are acceptable in your environment

- **Optional but recommended**
  - `libcamera-tools` – if any interaction with libcamera / libcamera-apps is anticipated
  - `htop`, `iotop` – for runtime resource observation during camera pipelines

### Example installation

```bash
sudo apt-get update
sudo apt-get install -y \
  usbutils pciutils \
  v4l-utils \
  ffmpeg \
  gstreamer1.0-tools gstreamer1.0-libav \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
  libcamera-tools \
  htop iotop
```

---

## Verification Commands

This section defines the expected checks to confirm that the system recognizes the camera and that basic video and audio capture work. These are not instructional step‑by‑step commands but should be used as a reference checklist.

### 1. Verify USB enumeration

- **Check that the device appears on the USB bus**

```bash
lsusb
```

**Expectations:**
- An entry corresponding to the USB HD Camera / OV5693 sensor is present.
- If needed, `lsusb -v` can be used to inspect descriptors and confirm UVC/UAC interfaces.

### 2. Confirm kernel modules and device nodes

- **Check video‑related modules**

```bash
lsmod | grep -E 'uvcvideo|videodev'
```

- **Check audio modules**

```bash
lsmod | grep snd_usb_audio
```

- **Check device nodes**

```bash
ls -l /dev/video*
```

**Expectations:**
- At least one `/dev/videoN` node (typically `/dev/video0`) exists for the camera.
- `uvcvideo` and `videodev` are loaded (if they are modular).
- `snd_usb_audio` is loaded if the microphone is present and recognized.

### 3. Inspect V4L2 capabilities

- **List detected V4L2 devices**

```bash
v4l2-ctl --list-devices
```

- **Inspect a given device (replace `/dev/video0` if different)**

```bash
v4l2-ctl --device=/dev/video0 --all
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

**Expectations:**
- The device name corresponds to the USB HD Camera / OV5693 sensor.
- Supported resolutions and pixel formats appropriate for a 5 MP camera are listed.

### 4. Quick video path validation

Use either FFmpeg or GStreamer to validate that frames can be streamed and encoded without errors. The specific sink may vary depending on whether the system is headless or has a display.

- **FFmpeg test capture to a temporary file**

```bash
ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -i /dev/video0 -frames:v 100 /tmp/test_capture.mkv
```

**Expectations:**
- FFmpeg initializes without errors and writes ~100 frames.
- Resulting file is viewable on a development workstation (not necessarily on the Pi itself).

- **GStreamer test pipeline (headless sink)**

```bash
gst-launch-1.0 v4l2src device=/dev/video0 ! \
  video/x-raw,width=1280,height=720,framerate=30/1 ! \
  videoconvert ! fakesink
```

**Expectations:**
- Pipeline runs without negotiation or stream errors for a sustained interval.
- CPU usage is within acceptable bounds for the Zero 2 W.

### 5. Microphone (audio) verification

- **List ALSA capture devices**

```bash
arecord -l
```

**Expectations:**
- A capture device entry corresponding to the USB camera’s microphone is present.

- **Short audio capture test**

```bash
arecord -D plughw:1,0 -f cd -d 5 /tmp/test_audio.wav
```

Adjust `plughw:X,Y` according to the device index from `arecord -l`.

**Expectations:**
- Recording completes without errors.
- The resulting file contains non‑silent audio when inspected on a host machine.

---

## Notes and Considerations

- **No CSI camera configuration required**
  - Because this is a USB UVC camera, no CSI camera enable flags or overlays are necessary.
  - `raspi-config` camera options and legacy `bcm2835-v4l2` are not required for this device.

- **Headless operation**
  - All verification commands are suitable for SSH/headless environments.
  - For interactive preview (if a display is available), tools like `qv4l2` or `ffplay` can be added to the environment, but they are not required by this baseline.

- **Reproducibility**
  - Any development or deployment system intended to run the camera pipeline should conform to:
    - The OS assumptions listed above
    - The package set (or a strict superset of it)
    - The same verification outcomes for USB enumeration, V4L2, and ALSA


