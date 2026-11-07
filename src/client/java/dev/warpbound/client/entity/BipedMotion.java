package dev.warpbound.client.entity;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.warpbound.Warpbound;
import net.minecraft.client.Minecraft;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.util.Mth;
import software.bernie.geckolib.animation.AnimationProcessor;
import software.bernie.geckolib.cache.object.GeoBone;

import java.io.Reader;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * Движения двуногих в броне (NPC и игрок в модели Астартес) без контроллеров GeckoLib: клипы из assets/warpbound/motion/<модель>.json
 * (пишет tools/models/blender/astartes/biped_motion.py, motion_json) проигрываются и смешиваются здесь, раз в кадр.
 * <p>
 * Зачем своё: GeckoLib считает время клипа как «прошедшее время × скорость», и подстройка скорости под тело сдвигает фазу рывком.
 * Здесь у шага одна фаза на все аллюры (у всех клипов 0 — касание левой пяткой), она копится плавно; аллюры смешиваются по скорости,
 * поэтому ходьба перетекает в бег без переключения. Сверху: присед, воздух (взлёт и падение), приземление добавкой по силе удара,
 * удар рукой с собственным весом (ноги на бегу не трогает), смерть.
 */
public final class BipedMotion {
    // ------------------------------------------------------------------ клипы

    public record Channel(boolean lower, float[] rot, float[] pos) {
    }

    public record Clip(String mode, float length, int frames, float[] weight, float speed, Map<String, Channel> bones) {
        boolean loop() {
            return mode.equals("loop");
        }

        /** Индексы и доля между кадрами для времени sec. */
        private float frame(float sec) {
            if (loop()) {
                float u = sec / length;
                u -= (float) Math.floor(u);
                return u * frames;
            }
            return Mth.clamp(sec / length, 0, 1) * (frames - 1);
        }

        public float weightAt(float sec) {
            if (weight == null) return 1;
            if (!loop() && (sec < 0 || sec >= length)) return 0;
            float f = frame(sec);
            int i0 = (int) f;
            return Mth.lerp(f - i0, weight[Math.min(i0, frames - 1)], weight[next(i0)]);
        }

        private int next(int i0) {
            return loop() ? (i0 + 1) % frames : Math.min(i0 + 1, frames - 1);
        }

        /** Добавить в позу кадр sec с весом w. mode: SUM — взвешенная сумма, LERP — сместить позу к кадру. lower — множитель для ног. */
        void into(Pose pose, float sec, float w, int how, float lower) {
            if (w <= 0) return;
            float f = frame(sec);
            int i0 = Math.min((int) f, frames - 1), i1 = next(i0);
            float k = f - (int) f;
            for (Map.Entry<String, Channel> e : bones.entrySet()) {
                Channel c = e.getValue();
                float bw = c.lower() ? w * lower : w;
                if (bw <= 0) continue;
                float[] v = pose.get(e.getKey());
                for (int a = 0; a < 3; a++) {
                    if (c.rot() != null) blend(v, a, Mth.lerp(k, c.rot()[i0 * 3 + a], c.rot()[i1 * 3 + a]), bw, how);
                    if (c.pos() != null) blend(v, 3 + a, Mth.lerp(k, c.pos()[i0 * 3 + a], c.pos()[i1 * 3 + a]), bw, how);
                }
            }
        }

        private static void blend(float[] v, int i, float x, float w, int how) {
            if (how == LERP) v[i] = Mth.lerp(w, v[i], x);
            else v[i] += w * x;
        }
    }

    static final int SUM = 0, LERP = 1;

    /** Поза: кость → (rotX, rotY, rotZ, posX, posY, posZ) во внутренних осях GeckoLib. */
    public static final class Pose {
        final Map<String, float[]> bones = new HashMap<>();

        float[] get(String bone) {
            return bones.computeIfAbsent(bone, b -> new float[6]);
        }

        void clear() {
            for (float[] v : bones.values()) java.util.Arrays.fill(v, 0);
        }

        void scale(float k) {
            for (float[] v : bones.values()) for (int i = 0; i < 6; i++) v[i] *= k;
        }

        void addScaled(Pose o, float k) {
            for (Map.Entry<String, float[]> e : o.bones.entrySet()) {
                float[] v = get(e.getKey()), w = e.getValue();
                for (int i = 0; i < 6; i++) v[i] += w[i] * k;
            }
        }
    }

    private static final Map<String, Map<String, Clip>> CACHE = new HashMap<>();

    public static Map<String, Clip> of(String model) {
        return CACHE.computeIfAbsent(model, BipedMotion::load);
    }

    public static void clear() {
        CACHE.clear();
    }

    private static Map<String, Clip> load(String model) {
        Map<String, Clip> out = new HashMap<>();
        Optional<Resource> res = Minecraft.getInstance().getResourceManager().getResource(Warpbound.id("motion/" + model + ".json"));
        if (res.isEmpty()) return out;
        try (Reader reader = res.get().openAsReader()) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            for (Map.Entry<String, JsonElement> c : root.entrySet()) {
                JsonObject o = c.getValue().getAsJsonObject();
                Map<String, Channel> bones = new HashMap<>();
                for (Map.Entry<String, JsonElement> b : o.getAsJsonObject("bones").entrySet()) {
                    JsonObject bo = b.getValue().getAsJsonObject();
                    bones.put(b.getKey(), new Channel("lower".equals(bo.get("group").getAsString()),
                            bo.has("rot") ? floats(bo.getAsJsonArray("rot")) : null, bo.has("pos") ? floats(bo.getAsJsonArray("pos")) : null));
                }
                out.put(c.getKey(), new Clip(o.get("mode").getAsString(), o.get("length").getAsFloat(), o.get("frames").getAsInt(),
                        o.has("weight") ? floats(o.getAsJsonArray("weight")) : null, o.has("speed") ? o.get("speed").getAsFloat() : 0, bones));
            }
        } catch (Exception e) {
            Warpbound.LOG.error("Не удалось прочитать движения {}: {}", model, e.toString());
        }
        return out;
    }

    private static float[] floats(JsonArray a) {
        float[] f = new float[a.size()];
        for (int i = 0; i < f.length; i++) f[i] = a.get(i).getAsFloat();
        return f;
    }

    // ------------------------------------------------------------------ состояние и смешивание

    /** Что сейчас делает тело (заполняет NPC или игрок). time и *Start — секунды от тиков сущности. */
    public static final class Input {
        public float time, speed, vy, deathSec = -1, swingStart = -1000;
        public boolean onGround = true, crouching, swingLeft;
        /** Особое состояние (игрок): null — обычная земля и воздух. Имена — клипы: sleep, sit, glide, swim, crawl, climb, tread, fly. */
        public String special;

        public void reset() {
            special = null;
            crouching = swingLeft = false;
            onGround = true;
            deathSec = -1;
        }
    }

    /** Особые состояния по убыванию важности; у каждого свой вес. */
    private static final String[] SPECIAL = {"sleep", "sit", "glide", "swim", "crawl", "climb", "tread", "fly"};

    private static final String[] GROUND = {"stroll", "walk", "run"};

    /** Плавные веса и фаза: по одному на сущность. */
    public static final class State {
        float last = Float.NaN, phase;
        final float[] gait = new float[GROUND.length + 1];      // покой и аллюры
        float crouch, ground = 1, rise, landStart = -1000, landPower, minVy;
        final float[] special = new float[SPECIAL.length];
        float climbPhase, swimPhase, climbMove, flyMove;
        boolean wasGround = true;
        final Pose pose = new Pose(), tmp = new Pose();
        { gait[0] = 1; }
    }

    private static float approach(float v, float target, float dt, float tau) {
        return v + (target - v) * (1 - (float) Math.exp(-dt / tau));
    }

    /** Целевые веса покоя и аллюров по скорости: линейно между соседними скоростями. */
    private static void gaitTargets(Map<String, Clip> clips, float speed, float[] out) {
        java.util.Arrays.fill(out, 0);
        float prevSpeed = 0;
        int prev = 0;
        if (speed < 0.15f) {
            out[0] = 1;
            return;
        }
        for (int i = 0; i < GROUND.length; i++) {
            Clip c = clips.get(GROUND[i]);
            if (c == null) continue;
            if (speed <= c.speed()) {
                float k = (speed - prevSpeed) / Math.max(0.01f, c.speed() - prevSpeed);
                out[prev] = 1 - k;
                out[i + 1] = k;
                return;
            }
            prevSpeed = c.speed();
            prev = i + 1;
        }
        out[prev] = 1;
    }

    /** Собрать позу и выставить кости. Возвращает false, если у модели нет файла движений (тогда работают клипы GeckoLib). */
    public static boolean animate(AnimationProcessor<?> processor, String model, State s, Input in) {
        Map<String, Clip> clips = of(model);
        if (clips.isEmpty()) return false;
        float dt = Float.isNaN(s.last) ? 0 : Mth.clamp(in.time - s.last, 0, 0.1f);
        s.last = in.time;
        float speed = in.speed < 0.15f ? 0 : in.speed;

        // ---- плавные веса
        float[] target = new float[s.gait.length];
        gaitTargets(clips, speed, target);
        for (int i = 0; i < s.gait.length; i++) s.gait[i] = approach(s.gait[i], target[i], dt, 0.12f);
        s.crouch = approach(s.crouch, in.crouching ? 1 : 0, dt, 0.08f);
        s.ground = approach(s.ground, in.onGround ? 1 : 0, dt, in.onGround ? 0.035f : 0.07f);
        s.rise = approach(s.rise, Mth.clamp((in.vy + 0.05f) / 0.25f, 0, 1), dt, 0.08f);
        // приземление: сила по скорости падения (прыжок на месте ~0,4 блока за тик, падение с 4 блоков ~0,8)
        if (!in.onGround) s.minVy = Math.min(s.minVy, in.vy);
        if (in.onGround && !s.wasGround) {
            s.landStart = in.time;
            s.landPower = Mth.clamp((-s.minVy - 0.1f) / 0.6f, 0.2f, 1.2f);
            s.minVy = 0;
        }
        s.wasGround = in.onGround;

        // ---- фаза шага: частота — взвешенная по аллюрам, ступни идут вровень с землёй
        Clip sneak = clips.get("sneak");
        float freq = 0, wsum = 0;
        for (int i = 0; i < GROUND.length; i++) {
            Clip c = clips.get(GROUND[i]);
            float w = s.gait[i + 1];
            if (c == null || w <= 0) continue;
            freq += w * Mth.clamp(speed / c.speed(), 0.5f, 1.5f) / c.length();
            wsum += w;
        }
        float groundFreq = wsum > 0.001f ? freq / wsum : 1 / 0.6f;
        float sneakFreq = sneak == null ? groundFreq : Mth.clamp(speed / sneak.speed(), 0.5f, 1.5f) / sneak.length();
        s.phase += dt * Mth.lerp(s.crouch, groundFreq, sneakFreq);
        s.phase -= (float) Math.floor(s.phase);

        // ---- земля: покой и аллюры; присед — свой покой и свой шаг
        Pose pose = s.pose, tmp = s.tmp;
        pose.clear();
        tmp.clear();
        Clip idle = clips.get("idle");
        if (idle != null) idle.into(tmp, in.time, s.gait[0], SUM, 1);
        for (int i = 0; i < GROUND.length; i++) {
            Clip c = clips.get(GROUND[i]);
            if (c != null) c.into(tmp, s.phase * c.length(), s.gait[i + 1], SUM, 1);
        }
        pose.addScaled(tmp, 1 - s.crouch);
        if (s.crouch > 0.001f) {
            tmp.clear();
            float moving = 1 - s.gait[0];
            Clip sIdle = clips.get("sneak_idle");
            if (sIdle != null) sIdle.into(tmp, in.time, 1 - moving, SUM, 1);
            if (sneak != null) sneak.into(tmp, s.phase * sneak.length(), moving, SUM, 1);
            pose.addScaled(tmp, s.crouch);
        }
        // ---- воздух: взлёт и падение
        if (s.ground < 0.999f) {
            pose.scale(s.ground);
            tmp.clear();
            Clip rise = clips.get("air_rise"), fall = clips.get("air_fall");
            if (rise != null) rise.into(tmp, in.time, s.rise, SUM, 1);
            if (fall != null) fall.into(tmp, in.time, 1 - s.rise, SUM, 1);
            pose.addScaled(tmp, 1 - s.ground);
        }
        // ---- особые состояния: каждое плавно вытесняет обычную позу
        float specialSum = 0;
        for (int i = 0; i < SPECIAL.length; i++) {
            s.special[i] = approach(s.special[i], SPECIAL[i].equals(in.special) ? 1 : 0, dt, 0.14f);
            specialSum += s.special[i];
        }
        float base = Mth.clamp(1 - specialSum, 0, 1);
        if (specialSum > 0.001f) {
            Clip climb = clips.get("climb"), swim = clips.get("swim"), crawl = clips.get("crawl");
            // лестница: фаза от подъёма (вниз — назад), стоит на месте — висит
            if (climb != null) s.climbPhase += in.vy * 20 * dt / Math.max(0.1f, climb.speed());
            s.climbMove = approach(s.climbMove, Mth.clamp(Math.abs(in.vy) * 20 / 0.8f, 0, 1), dt, 0.1f);
            float travel = Math.max(in.speed, Math.abs(in.vy) * 20);
            Clip stroke = "crawl".equals(in.special) ? crawl : swim;
            if (stroke != null) s.swimPhase += dt * Math.max(0.25f, travel) / Math.max(0.1f, stroke.speed());
            s.flyMove = approach(s.flyMove, Mth.clamp(in.speed / 6f, 0, 1), dt, 0.25f);
            pose.scale(base);
            for (int i = 0; i < SPECIAL.length; i++) {
                float w = s.special[i];
                if (w <= 0.001f) continue;
                switch (SPECIAL[i]) {
                    case "climb" -> {
                        if (climb != null) climb.into(pose, s.climbPhase * climb.length(), w * s.climbMove, SUM, 1);
                        Clip hang = clips.get("climb_idle");
                        if (hang != null) hang.into(pose, in.time, w * (1 - s.climbMove), SUM, 1);
                    }
                    case "swim" -> { if (swim != null) swim.into(pose, s.swimPhase * swim.length(), w, SUM, 1); }
                    case "crawl" -> { if (crawl != null) crawl.into(pose, s.swimPhase * crawl.length(), w, SUM, 1); }
                    case "fly" -> {
                        Clip hover = clips.get("fly"), move = clips.get("fly_move");
                        if (hover != null) hover.into(pose, in.time, w * (1 - s.flyMove), SUM, 1);
                        if (move != null) move.into(pose, in.time, w * s.flyMove, SUM, 1);
                    }
                    default -> {
                        Clip c = clips.get(SPECIAL[i]);
                        if (c != null) c.into(pose, in.time, w, SUM, 1);
                    }
                }
            }
        }
        // ---- приземление поверх
        Clip land = clips.get("land");
        if (land != null) {
            float sec = in.time - s.landStart;
            if (sec >= 0 && sec < land.length()) land.into(pose, sec, s.landPower * s.ground * base, SUM, 1);
        }
        // ---- удар: свой вес, ноги только на месте и на земле
        Clip melee = clips.get(in.swingLeft ? "melee_l" : "melee_r");
        if (melee != null) {
            float sec = in.time - in.swingStart;
            float w = melee.weightAt(sec);
            if (w > 0) melee.into(pose, sec, w, LERP, BipedLayers.lowerWeight(speed) * s.ground * base);
        }
        // ---- смерть перекрывает всё
        Clip death = clips.get("death");
        if (in.deathSec >= 0 && death != null) {
            pose.clear();
            death.into(pose, in.deathSec, 1, SUM, 1);
        }
        for (Map.Entry<String, float[]> e : pose.bones.entrySet()) {
            GeoBone b = processor.getBone(e.getKey());
            if (b == null) continue;
            float[] v = e.getValue();
            b.setRotX(v[0]);
            b.setRotY(v[1]);
            b.setRotZ(v[2]);
            b.setPosX(v[3]);
            b.setPosY(v[4]);
            b.setPosZ(v[5]);
        }
        return true;
    }
}
