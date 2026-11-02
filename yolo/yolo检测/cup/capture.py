"""用 USB 摄像头拍水杯原图，供 labelImg 标注。

先把摄像头接到虚拟机，再进入虚拟环境，在本目录运行：

    source ~/venvs/yolo/bin/activate
    python capture.py

空格：保存当前原始画面。文件里不画框。
q：退出

照片在 raw/，文件名 img_00.jpg 起。已经有的编号不会被覆盖。
拍的时候换距离、角度和位置，不要连续按空格存下几乎一样的画面。
"""

from pathlib import Path

import cv2

HERE = Path(__file__).resolve().parent
OUT = HERE / "raw"


def next_index(folder):
    numbers = []
    for path in folder.glob("img_*.jpg"):
        stem = path.stem.replace("img_", "")
        if stem.isdigit():
            numbers.append(int(stem))
    return max(numbers, default=-1) + 1


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "classes.txt").write_text("cup\n", encoding="utf-8")
    index = next_index(OUT)

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    # 这台虚拟机里强制 MJPG 会出横条。用摄像头默认格式，640x480。
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    if not cap.isOpened():
        raise SystemExit("打不开摄像头。先确认虚拟机里连的是 RGB Camera，并且存在 /dev/video0。")

    print(f"保存目录：{OUT}")
    print("窗口里按空格保存一张，按 q 退出。目标大约 50 张。")
    while True:
        ok, frame = cap.read()
        if not ok:
            print("读不到画面。请检查 USB 是否仍连接在虚拟机上。")
            break
        view = frame.copy()
        cv2.putText(
            view,
            f"saved {index}   SPACE save   Q quit",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        cv2.imshow("capture cup", view)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(" "):
            path = OUT / f"img_{index:02d}.jpg"
            cv2.imwrite(str(path), frame)
            print(f"已保存 {path.name}")
            index += 1
        elif key in (ord("q"), ord("Q")):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"raw 里一共 {index} 张。接下来用 labelImg 标 cup，txt 和 jpg 放在同一目录。")


if __name__ == "__main__":
    main()
