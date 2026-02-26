

import cv2
import mediapipe as mp
import numpy as np
import time
import math
import random
from collections import deque

# =========================================================================
# 1. CORE MATHEMATICS & 3D PROJECTION
# =========================================================================
class MathUtils:
    @staticmethod
    def project_3d_to_2d(x, y, z, fov=250, viewer_distance=400):
        """Projects a 3D coordinate onto a 2D plane using a basic perspective divide."""
        factor = fov / (viewer_distance + z) if (viewer_distance + z) != 0 else 1
        x_proj = x * factor
        y_proj = y * factor
        return int(x_proj), int(y_proj), factor

    @staticmethod
    def rotate_3d(x, y, z, angle_x, angle_y, angle_z):
        """Rotates a point in 3D space around the origin."""
        # X rotation
        cos_x, sin_x = math.cos(angle_x), math.sin(angle_x)
        y1 = y * cos_x - z * sin_x
        z1 = y * sin_x + z * cos_x
        # Y rotation
        cos_y, sin_y = math.cos(angle_y), math.sin(angle_y)
        x2 = x * cos_y + z1 * sin_y
        z2 = -x * sin_y + z1 * cos_y
        # Z rotation
        cos_z, sin_z = math.cos(angle_z), math.sin(angle_z)
        x3 = x2 * cos_z - y1 * sin_z
        y3 = x2 * sin_z + y1 * cos_z
        return x3, y3, z2

    @staticmethod
    def bezier_curve(p0, p1, p2, p3, num_points=20):
        """Generates points along a cubic Bezier curve (used for Crimson Bands)."""
        pts = []
        for i in range(num_points):
            t = i / float(num_points - 1)
            u = 1 - t
            x = (u**3 * p0[0] + 3*u**2*t * p1[0] + 3*u*t**2 * p2[0] + t**3 * p3[0])
            y = (u**3 * p0[1] + 3*u**2*t * p1[1] + 3*u*t**2 * p2[1] + t**3 * p3[1])
            pts.append((int(x), int(y)))
        return pts

    @staticmethod
    def create_radial_gradient(radius):
        """Creates a smooth alpha mask for seamless blending."""
        y, x = np.ogrid[-radius:radius, -radius:radius]
        mask = x**2 + y**2 <= radius**2
        
        # Create gradient falloff
        distance = np.sqrt(x**2 + y**2)
        gradient = np.clip(1.0 - (distance / radius), 0, 1)
        
        alpha_channel = np.zeros((radius*2, radius*2), dtype=np.float32)
        alpha_channel[mask] = gradient[mask]
        return alpha_channel

# =========================================================================
# 2. ELDRITCH GEOMETRY & SPELL GRAPHICS
# =========================================================================
class EldritchMandala:
    @staticmethod
    def draw_complex_mandala(img, cx, cy, global_angle, radius, color=(0, 160, 255)):
        """Draws a complex, multi-layered movie-accurate magic shield."""
        # LAYER 1: The Outer Orbiting Rings (3D Illusion)
        tilt_x = math.sin(global_angle * 0.5) * 0.8
        tilt_y = math.cos(global_angle * 0.3) * 0.5
        
        orbit_pts = []
        for i in range(0, 360, 10):
            rad = math.radians(i + global_angle * 50)
            x, y, z = MathUtils.rotate_3d(math.cos(rad) * radius * 1.1, math.sin(rad) * radius * 1.1, 0, tilt_x, tilt_y, 0)
            px, py, _ = MathUtils.project_3d_to_2d(x, y, z)
            orbit_pts.append([cx + px, cy + py])
        cv2.polylines(img, [np.array(orbit_pts)], True, color, 1, cv2.LINE_AA)

        # LAYER 2: The Core Structure
        cv2.circle(img, (cx, cy), radius, color, 2, cv2.LINE_AA)
        cv2.circle(img, (cx, cy), int(radius * 0.88), color, 1, cv2.LINE_AA)
        cv2.circle(img, (cx, cy), int(radius * 0.2), color, 2, cv2.LINE_AA)

        # LAYER 3: Rotating Inner Squares & Octagons
        pts_square1, pts_square2, pts_octa = [], [], []
        for i in range(4):
            # Square 1
            theta1 = global_angle + i * (math.pi / 2)
            pts_square1.append([cx + int(math.cos(theta1)*radius), cy + int(math.sin(theta1)*radius)])
            # Square 2 (Offset to create 8-point star)
            theta2 = -global_angle + i * (math.pi / 2) + (math.pi/4)
            pts_square2.append([cx + int(math.cos(theta2)*int(radius*0.88)), cy + int(math.sin(theta2)*int(radius*0.88))])

        for i in range(8):
            # Inner Octagon
            theta3 = (global_angle * 2) + i * (math.pi / 4)
            pts_octa.append([cx + int(math.cos(theta3)*int(radius*0.5)), cy + int(math.sin(theta3)*int(radius*0.5))])

        cv2.polylines(img, [np.array(pts_square1)], True, color, 2, cv2.LINE_AA)
        cv2.polylines(img, [np.array(pts_square2)], True, color, 2, cv2.LINE_AA)
        cv2.polylines(img, [np.array(pts_octa)], True, color, 1, cv2.LINE_AA)

        # LAYER 4: Connecting Runes / Sigil Lines
        for i in range(8):
            ang = global_angle + i * (math.pi / 4)
            p1 = (cx + int(math.cos(ang)*int(radius*0.2)), cy + int(math.sin(ang)*int(radius*0.2)))
            p2 = (cx + int(math.cos(ang)*int(radius*0.5)), cy + int(math.sin(ang)*int(radius*0.5)))
            cv2.line(img, p1, p2, color, 1, cv2.LINE_AA)

class MagicInteractions:
    @staticmethod
    def draw_crimson_bands(magic_layer, p1, p2, time_val):
        """Draws chaotic whipping bands utilizing Bezier curves to look natural."""
        dist = math.hypot(p1[0]-p2[0], p1[1]-p2[1])
        if dist == 0: return

        # Draw a heavy central core
        cv2.line(magic_layer, p1, p2, (0, 0, 150), 6, cv2.LINE_AA)
        cv2.line(magic_layer, p1, p2, (50, 50, 255), 2, cv2.LINE_AA)

        # Generate whipping tendrils
        for i in range(5):
            # Calculate control points that oscillate based on sine/cosine waves
            offset_mag = dist * 0.4
            cx1 = p1[0] + int(math.cos(time_val * (2+i)) * offset_mag)
            cy1 = p1[1] + int(math.sin(time_val * (3+i)) * offset_mag)
            
            cx2 = p2[0] + int(math.cos(time_val * (4+i) + math.pi) * offset_mag)
            cy2 = p2[1] + int(math.sin(time_val * (5+i) + math.pi) * offset_mag)

            curve_pts = MathUtils.bezier_curve(p1, (cx1, cy1), (cx2, cy2), p2, 15)
            
            for j in range(1, len(curve_pts)):
                cv2.line(magic_layer, curve_pts[j-1], curve_pts[j], (0, 0, 255), 2, cv2.LINE_AA)

    @staticmethod
    def draw_time_stone(magic_layer, mx, my, global_angle):
        """Creates an eye of Agamotto 3D concentric ring effect."""
        color = (0, 255, 0)
        # Core Eye
        cv2.circle(magic_layer, (mx, my), 30, color, 2, cv2.LINE_AA)
        cv2.ellipse(magic_layer, (mx, my), (60, 20), math.degrees(global_angle), 0, 360, color, 2, cv2.LINE_AA)
        cv2.ellipse(magic_layer, (mx, my), (60, 20), math.degrees(-global_angle), 0, 360, color, 2, cv2.LINE_AA)
        
        # Outer Runes
        for i in range(6):
            ang = -global_angle * 2 + i * (math.pi / 3)
            px = mx + int(math.cos(ang) * 90)
            py = my + int(math.sin(ang) * 90)
            cv2.circle(magic_layer, (px, py), 5, (50, 255, 50), -1)
            cv2.line(magic_layer, (mx, my), (px, py), (0, 100, 0), 1)

# =========================================================================
# 3. ADVANCED PARTICLE SYSTEM
# =========================================================================
class Spark:
    def __init__(self, x, y, vx, vy, life, size=2, is_trace=False):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life, self.max_life = life, life
        self.size = size
        self.is_trace = is_trace # Trace sparks ignore gravity for longer

    def update(self):
        self.x += self.vx
        self.y += self.vy
        
        if not self.is_trace:
            self.vy += 0.6  # Gravity
            self.vx *= 0.92 # Drag
        else:
            self.vx *= 0.85
            self.vy *= 0.85

        # Flicker effect
        self.life -= random.uniform(0.5, 1.5)
        return self.life > 0

    def get_color(self):
        ratio = self.life / self.max_life
        if ratio > 0.8: return (255, 255, 255)    # White hot core
        elif ratio > 0.4: return (0, 165, 255)    # Neon Orange
        elif ratio > 0.1: return (0, 80, 200)     # Deep Ember
        else: return (0, 0, 80)                   # Smoke/Dark Red

class PortalGateway:
    def __init__(self, cx, cy, radius):
        self.cx, self.cy = cx, cy
        self.target_radius = radius
        self.current_radius = 5
        self.angle = 0.0
        self.sparks = []
        self.is_closing = False
        self.life_timer = time.time()
        self.max_duration = 10.0 # Stay open longer

    def update_and_draw(self, magic_layer, base_frame):
        time_alive = time.time() - self.life_timer
        if time_alive > self.max_duration:
            self.is_closing = True

        # Fluid Spring physics for radius
        if not self.is_closing:
            diff = self.target_radius - self.current_radius
            self.current_radius += diff * 0.1
        else:
            self.current_radius *= 0.75 # Snap shut

        self.angle += 0.15 
        r = int(self.current_radius)

        if r > 15:
            # --- THE DIMENSIONAL INTERIOR ---
            # Instead of a black hole, we create a cosmic lens distortion
            # We isolate a circle, tint it dark purple/blue, scale it, and blend it back
            
            # Safe boundary check
            h, w = base_frame.shape[:2]
            y1, y2 = max(0, self.cy - r), min(h, self.cy + r)
            x1, x2 = max(0, self.cx - r), min(w, self.cx + r)
            
            if y2 > y1 and x2 > x1:
                roi = base_frame[y1:y2, x1:x2].copy()
                
                # Darken and tint the region (Cosmic Void effect)
                cosmic_tint = np.zeros_like(roi)
                cosmic_tint[:] = (80, 20, 40) # Broadcasting safely applies the dark BGR tint
                roi = cv2.addWeighted(roi, 0.3, cosmic_tint, 0.7, 0)
                
                # Apply radial gradient mask to blend the edges smoothly
                mask = MathUtils.create_radial_gradient(r)
                mask_roi = mask[(y1 - (self.cy-r)):(y2 - (self.cy-r)), (x1 - (self.cx-r)):(x2 - (self.cx-r))]
                mask_roi = np.stack([mask_roi]*3, axis=2)
                
                # Blend the cosmic interior into the main frame
                base_frame[y1:y2, x1:x2] = np.where(mask_roi > 0.1, 
                                                    (roi * mask_roi + base_frame[y1:y2, x1:x2] * (1 - mask_roi)).astype(np.uint8), 
                                                    base_frame[y1:y2, x1:x2])

            # --- THE RING GEOMETRY ---
            # Inner white hot core
            cv2.circle(magic_layer, (self.cx, self.cy), r, (150, 220, 255), 2, cv2.LINE_AA)
            # Outer chaotic bands
            for i in range(3):
                offset = r + int(math.sin(self.angle * (i+1)) * 5)
                cv2.circle(magic_layer, (self.cx, self.cy), offset, (0, 100, 255), 4, cv2.LINE_AA)

        # --- PARTICLE EMISSION ---
        if not self.is_closing and r > 20:
            for _ in range(15): # High density
                emit_ang = random.uniform(0, math.pi * 2)
                px = self.cx + math.cos(emit_ang) * r
                py = self.cy + math.sin(emit_ang) * r
                
                # Tangential spin velocity
                tangent = emit_ang + (math.pi / 2)
                speed = random.uniform(8, 20)
                vx = math.cos(tangent) * speed + random.uniform(-4, 4)
                vy = math.sin(tangent) * speed + random.uniform(-4, 4)
                
                # Occasional explosive sparks shooting straight out
                if random.random() > 0.9:
                    vx = math.cos(emit_ang) * (speed * 1.5)
                    vy = math.sin(emit_ang) * (speed * 1.5)

                self.sparks.append(Spark(px, py, vx, vy, random.randint(20, 50), random.randint(1, 4)))

        # Update sparks
        alive_sparks = []
        for s in self.sparks:
            if s.update():
                cv2.circle(magic_layer, (int(s.x), int(s.y)), s.size, s.get_color(), -1)
                alive_sparks.append(s)
        self.sparks = alive_sparks

        return self.current_radius > 2 or len(self.sparks) > 0

# =========================================================================
# 4. GRIMOIRE HUD (NEXT-GEN UI)
# =========================================================================
class GrimoireUI:
    def __init__(self):
        self.energy_level = 0.0
        self.sine_offset = 0.0

    def render(self, frame, active_spell, is_drawing):
        h, w = frame.shape[:2]
        self.sine_offset += 0.2

        # Left Cyber-Magic Panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (350, h), (15, 5, 20), -1) # Deep dark purple tint
        
        # Grid lines on overlay
        for i in range(0, h, 40):
            cv2.line(overlay, (0, i), (350, i), (40, 20, 50), 1)
            
        frame[:] = cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)

        # Main Header
        cv2.putText(frame, "CODEX OF CAGLIOSTRO", (20, 40), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 220, 255), 1, cv2.LINE_AA)
        cv2.line(frame, (20, 55), (330, 55), (0, 150, 255), 2)

        # Dynamic Energy Waveform (Sine wave readout)
        cv2.putText(frame, "MYSTIC RESONANCE:", (20, 90), cv2.FONT_HERSHEY_PLAIN, 1.2, (150, 150, 150), 1)
        
        # Determine energy amplitude based on activity
        target_energy = 50 if active_spell or is_drawing else 10
        self.energy_level += (target_energy - self.energy_level) * 0.1
        
        wave_pts = []
        for x in range(20, 330, 5):
            y = 120 + int(math.sin(x * 0.05 + self.sine_offset) * (self.energy_level * random.uniform(0.8, 1.2)))
            wave_pts.append([x, y])
        cv2.polylines(frame, [np.array(wave_pts)], False, (0, 255, 100), 2, cv2.LINE_AA)

        # Magic Protocols
        y_offset = 180
        cv2.putText(frame, "ACTIVE INCANTATIONS:", (20, y_offset), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 200, 255), 1)
        
        spells = [
            ("SLING RING", "Idx+Mid Up -> Draw"),
            ("TAO MANDALA", "Open Palms"),
            ("TIME STONE", "Dual Pinch Close"),
            ("CRIMSON BANDS", "Dual Pinch Pull")
        ]
        
        y_offset += 40
        for name, req in spells:
            is_active = (active_spell == name) or (name == "SLING RING" and is_drawing)
            color = (0, 255, 0) if is_active else (80, 80, 80)
            indicator = "[ ACTIVE ]" if is_active else "[ STANDBY ]"
            
            cv2.putText(frame, name, (20, y_offset), cv2.FONT_HERSHEY_DUPLEX, 0.6, color, 1)
            cv2.putText(frame, req, (20, y_offset + 20), cv2.FONT_HERSHEY_PLAIN, 1.0, color, 1)
            cv2.putText(frame, indicator, (230, y_offset), cv2.FONT_HERSHEY_PLAIN, 1.0, color, 1)
            y_offset += 60

        # Bottom UI Decorative Element
        cv2.circle(frame, (175, h - 80), 40, (0, 150, 255), 1, cv2.LINE_AA)
        cv2.circle(frame, (175, h - 80), int(40 + math.sin(self.sine_offset)*5), (0, 100, 255), 1)
        inner_ang = self.sine_offset * 0.5
        px1, py1 = 175 + int(math.cos(inner_ang)*40), (h-80) + int(math.sin(inner_ang)*40)
        px2, py2 = 175 + int(math.cos(inner_ang + math.pi)*40), (h-80) + int(math.sin(inner_ang + math.pi)*40)
        cv2.line(frame, (px1, py1), (px2, py2), (0, 150, 255), 1)

# =========================================================================
# 5. POSE ANALYSIS ENGINE
# =========================================================================
def analyze_hand(landmarks, w, h):
    """Calculates boolean states for fingers and precise coordinates."""
    fingers = {
        'thumb': landmarks[4].y < landmarks[3].y, 
        'index': landmarks[8].y < landmarks[6].y,
        'middle': landmarks[12].y < landmarks[10].y,
        'ring': landmarks[16].y < landmarks[14].y,
        'pinky': landmarks[20].y < landmarks[18].y
    }
    
    is_sling = fingers['index'] and fingers['middle'] and not fingers['ring'] and not fingers['pinky']
    is_open = all(fingers.values())
    pinch_dist = math.hypot(landmarks[4].x - landmarks[8].x, landmarks[4].y - landmarks[8].y)
    
    return {
        'sling': is_sling, 
        'open': is_open, 
        'pinched': pinch_dist < 0.05,
        'idx_tip': (int(landmarks[8].x * w), int(landmarks[8].y * h)),
        'palm': (int(landmarks[9].x * w), int(landmarks[9].y * h))
    }

# =========================================================================
# 6. MAIN APPLICATION LOOP
# =========================================================================
def main():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    w, h = 1280, 720

    hands = mp.solutions.hands.Hands(max_num_hands=2, min_detection_confidence=0.75, min_tracking_confidence=0.75)
    
    portals = []
    trace_points = []
    trace_sparks = []
    
    global_time = 0.0
    history = deque(maxlen=120) # 4 seconds of time stone history
    reversing_time = False

    ui = GrimoireUI()

    print("\n[+] MYSTIC ARTS ENGINE INITIALIZED.")
    print("[!] Stand back. Ensure good lighting.")
    print("[!] Press ESC to close reality.\n")

    while cap.isOpened():
        success, raw_frame = cap.read()
        if not success: break
        
        # Pre-process frame
        raw_frame = cv2.flip(cv2.resize(raw_frame, (w, h)), 1)
        global_time += 0.1

        # -------------------------------------------------------------
        # TIME STONE: History Management
        # -------------------------------------------------------------
        if reversing_time and len(history) > 0:
            frame = history.pop()
            # Cinematic Green Reality Warp
            green_warp = np.zeros_like(frame, dtype=np.uint8)
            green_warp[:,:] = (0, 80, 0) # BGR
            # Add distortion lines (VHS/Time crunch effect)
            for i in range(0, h, 10):
                if random.random() > 0.8:
                    cv2.line(green_warp, (0, i), (w, i), (0, 150, 0), 1)
            frame = cv2.addWeighted(frame, 0.6, green_warp, 0.4, 0)
        else:
            history.append(raw_frame.copy())
            frame = raw_frame.copy()

        # -------------------------------------------------------------
        # THE MAGIC LAYER (Additive Compositing)
        # -------------------------------------------------------------
        # We draw all pure light/fire onto a black background, blur it, 
        # and mathematically ADD it to the camera frame.
        magic_layer = np.zeros_like(frame, dtype=np.uint8)
        
        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        poses = [analyze_hand(hl.landmark, w, h) for hl in results.multi_hand_landmarks] if results.multi_hand_landmarks else []

        active_spell = None
        is_drawing = False

        # -------------------------------------------------------------
        # GESTURE ROUTING & LOGIC
        # -------------------------------------------------------------
        if poses:
            sling_held = any(p['sling'] for p in poses)

            # SPELL 1: SLING RING PORTAL DRAWING
            if sling_held:
                is_drawing = True
                hand = next(p for p in poses if p['sling'])
                px, py = hand['idx_tip']
                trace_points.append((px, py))
                
                # Render the hot fiery trace trail
                if len(trace_points) > 2:
                    for i in range(1, len(trace_points)):
                        # Force the minimum thickness to be 1
                        thickness = max(1, int(min(6, i * 0.15))) 
                        cv2.line(magic_layer, trace_points[i-1], trace_points[i], (0, 150, 255), thickness, cv2.LINE_AA)
                # Emit sparks from the tracing finger
                trace_sparks.append(Spark(px, py, random.uniform(-2,2), random.uniform(-2,2), random.randint(10, 20), 2, is_trace=True))
                cv2.circle(magic_layer, (px, py), 8, (255, 255, 255), -1)
            else:
                # Trigger Portal generation when hand is dropped
                if len(trace_points) > 30:
                    xs = [p[0] for p in trace_points]
                    ys = [p[1] for p in trace_points]
                    cx, cy = int(sum(xs)/len(xs)), int(sum(ys)/len(ys))
                    radius = int(math.hypot(max(xs)-min(xs), max(ys)-min(ys)) / 1.7)
                    if radius > 50:
                        portals.append(PortalGateway(cx, cy, radius))
                trace_points.clear()

            # SPELL 2: TAO MANDALAS
            if all(p['open'] for p in poses) and not sling_held:
                active_spell = "TAO MANDALA"
                for p in poses:
                    EldritchMandala.draw_complex_mandala(magic_layer, p['palm'][0], p['palm'][1], global_time, 160)

            # SPELLS 3 & 4: TWO HAND INTERACTIONS
            if len(poses) == 2:
                p1, p2 = poses[0], poses[1]
                dist = math.hypot(p1['palm'][0] - p2['palm'][0], p1['palm'][1] - p2['palm'][1])

                if p1['pinched'] and p2['pinched']:
                    if dist < 220:
                        active_spell = "TIME STONE"
                        reversing_time = True
                        mx, my = (p1['palm'][0]+p2['palm'][0])//2, (p1['palm'][1]+p2['palm'][1])//2
                        MagicInteractions.draw_time_stone(magic_layer, mx, my, global_time)
                    else:
                        active_spell = "CRIMSON BANDS"
                        reversing_time = False
                        MagicInteractions.draw_crimson_bands(magic_layer, p1['palm'], p2['palm'], global_time)
                else:
                    reversing_time = False
        else:
            reversing_time = False
            trace_points.clear()

        # Update Trace Sparks
        alive_trace_sparks = []
        for ts in trace_sparks:
            if ts.update():
                cv2.circle(magic_layer, (int(ts.x), int(ts.y)), ts.size, ts.get_color(), -1)
                alive_trace_sparks.append(ts)
        trace_sparks = alive_trace_sparks

        # -------------------------------------------------------------
        # PORTAL RENDERING & COMPOSITING
        # -------------------------------------------------------------
        # Update portals (this modifies base_frame to create the cosmic void interior)
        portals = [p for p in portals if p.update_and_draw(magic_layer, frame)]

        # Apply realistic Bloom / Glow to the magic
        # We blur the magic layer and add it back to itself to make the core hot and edges soft
        glow = cv2.GaussianBlur(magic_layer, (21, 21), 0)
        magic_layer = cv2.add(magic_layer, glow)

        # Finally, True Additive Compositing onto the camera feed
        frame = cv2.add(frame, magic_layer)

        # -------------------------------------------------------------
        # USER INTERFACE RENDER PASS
        # -------------------------------------------------------------
        ui.render(frame, active_spell, is_drawing)

        cv2.imshow("MYSTIC ARTS ENGINE - ELDRITCH EDITION", frame)
        if cv2.waitKey(1) & 0xFF == 27: # ESC to quit
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()