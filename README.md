# 👁️ MysticEngine: The Augmented Reality Grimoire

**MysticEngine** is a real-time, interactive augmented reality experience built with Python, OpenCV, and MediaPipe. By tapping into the local fabric of reality (your webcam), this engine tracks your hand gestures to cast cinematic, movie-accurate spells and dimensional portals in real-time.

No physical props required—just your hands and the computational power of the Mystic Arts.

## ✨ The Spells (Features)

The engine monitors your hand landmarks and continuously analyzes finger states (open, pinched, or closed) to route your intent into active magic:

* **Sling Ring Gateways:** Hold your Index and Middle fingers up (Sling Ring gesture) and draw a circular path in the air. A portal to another dimension will spark, tear open, and collapse dynamically.
* **Tao Mandalas:** Open both palms to the camera to summon rotating, multi-layered, 3D-projected Eldritch shields of pure energy.
* **The Time Stone:** Bring both hands into frame and pinch your fingers together closely. You will summon the Eye of Agamotto, complete with green temporal distortion that reverses the camera's visual history.
* **Crimson Bands of Cyttorak:** Pinch your fingers with both hands and pull them apart. Chaotic, Bezier-curved lightning bands will chain between your hands, reacting to the distance.

## 🛠️ The Ritual (Installation)

To wield the MysticEngine, you must first prepare your environment. 

1. **Clone the Grimoire:**
   ```bash
   git clone [https://github.com/chaz-ux/MysticEngine.git](https://github.com/chaz-ux/MysticEngine.git)
   cd MysticEngine

   

2. **Summon the Dependencies:**
Ensure you have Python 3.8+ installed, then cast the following:
```bash
pip install opencv-python mediapipe numpy

```



## 🔮 Casting (Usage)

Ensure your webcam is not being used by another application, stand in a well-lit room, and execute the engine:

```bash
python mystic_engine.py

```

* **Heads Up Display (HUD):** The left side of your screen will display the Codex of Cagliostro UI, monitoring your Mystic Resonance and highlighting which incantations are currently on standby or active.
* **To end the session:** Press the `ESC` key to close the dimensional rift and return to normal reality.

## 📜 Arcane Architecture

* **Core Mathematics:** Custom 3D-to-2D projection math and Bezier curve generation.
* **Particle System:** A bespoke physics engine for calculating gravity, drag, and lifespans of sparks.
* **Additive Compositing:** Spells are drawn onto a pure black layer, Gaussian blurred for bloom, and mathematically added to the video feed for a true "holographic" lighting effect.

