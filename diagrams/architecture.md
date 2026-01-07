## Embedded Linux Camera Pipeline – High-Level Architecture

```text
+--------------------+       +----------------------+       +--------------------------+       +-----------------------------+
|  Camera Sensor     |       |  Kernel Space        |       |  Userspace Application   |       |  Robotics Perception Stack  |
|  (OV5693, optics)  |       |  (Drivers & V4L2)    |       |  (Capture & Handling)    |       |  (Future Integration)       |
+--------------------+       +----------------------+       +--------------------------+       +-----------------------------+
           |                             |                                |                                |
           |  Photons -> pixel data      |                                |                                |
           v                             |                                |                                |
  [Image sensor electronics]            |                                |                                |
           |                             |                                |                                |
           |  Digital frames over CSI/USB|                                |                                |
           v                             v                                |                                |
                                +----------------------+                  |                                |
                                |  Kernel Camera       |                  |                                |
                                |  Driver (e.g.        |                  |                                |
                                |  uvcvideo / CSI)     |                  |                                |
                                +----------------------+                  |                                |
                                             |                            |                                |
                                             |  V4L2 / media controller   |                                |
                                             v                            |                                |
                                +----------------------+                  |                                |
                                |  V4L2 / Libcamera    |                  |                                |
                                |  Interfaces          |                  |                                |
                                +----------------------+                  |                                |
                                             |                            |                                |
                                             |  /dev/video*, libcamera    |                                |
                                             v                            v                                |
                                    +--------------------------+         |                                |
                                    | Userspace Capture Tool   |         |                                |
                                    | (e.g., libcamera-still,  |---------+                                |
                                    |  C++ inspection utility, |   Frames / metadata                      |
                                    |  Python helpers)         |                                          |
                                    +--------------------------+                                          |
                                                         |                                               |
                                                         |  Structured image stream + timing/pose       |
                                                         v                                               v
                                              +-----------------------------+                  +--------------------------+
                                              |  Robotics Perception Node  |                  |  Downstream Consumers    |
                                              |  (Future)                  |----------------->|  (Mapping, Planning,     |
                                              |  - Subscribes to frames    |   Features /     |   Control, Logging, etc.)|
                                              |  - Runs CV/ML pipelines    |   detections     +--------------------------+
                                              +-----------------------------+
```

### Key Boundaries

- **Sensor → Kernel**
  - Physical signal path (CSI/USB) carrying raw or compressed frames.
  - Handled by hardware-specific camera drivers and related kernel subsystems.

- **Kernel → Userspace**
  - Exposed via character devices (e.g., `/dev/video*`) and libcamera/V4L2 APIs.
  - Userspace tools request frames, configure formats, and control streaming.

- **Userspace → Robotics Perception**
  - Userspace applications package frames with timestamps and optional metadata.
  - Robotics perception nodes consume these streams to build higher-level
    understanding (features, objects, scene layout) for control and planning.


