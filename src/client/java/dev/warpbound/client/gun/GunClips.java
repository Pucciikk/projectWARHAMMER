package dev.warpbound.client.gun;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.warpbound.Warpbound;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;

import java.io.Reader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Клипы анимации оружия из assets/warpbound/gun_anim/&lt;модель&gt;.json. Пишет их tools/models/blender/guns/ из тех же функций,
 * что показывают движение в Blender. Сэмплирует равномерные дорожки сам, а не через контроллеры GeckoLib:
 * так перезарядка, отдача и покачивание сводятся в один расчёт кадра.
 */
final class GunClips {
    record Event(float time, String name) {
    }

    /** На кость: {x, y, z, rotX, rotY, rotZ} по кадрам, в осях Blender (метры и градусы). */
    record Clip(float length, boolean loop, float fps, Map<String, float[][]> tracks, List<Event> events) {
        boolean sample(String bone, float seconds, float[] out) {
            float[][] tr = tracks.get(bone);
            if (tr == null || tr.length == 0) return false;
            float f = Math.max(0, seconds) * fps;
            int i = Math.min((int) f, tr.length - 1), j = Math.min(i + 1, tr.length - 1);
            float k = Math.min(1, f - i);
            for (int c = 0; c < 6; c++) out[c] = tr[i][c] + (tr[j][c] - tr[i][c]) * k;
            return true;
        }
    }

    private static final Map<String, Map<String, Clip>> CACHE = new HashMap<>();
    private static final Clip EMPTY = new Clip(0.1f, false, 30, Map.of(), List.of());

    private GunClips() {
    }

    static void clear() {
        CACHE.clear();
    }

    static Clip get(String model, String clip) {
        return CACHE.computeIfAbsent(model, GunClips::load).getOrDefault(clip, EMPTY);
    }

    private static Map<String, Clip> load(String model) {
        Map<String, Clip> out = new HashMap<>();
        ResourceLocation path = Warpbound.id("gun_anim/" + model + ".json");
        try (Reader reader = Minecraft.getInstance().getResourceManager().openAsReader(path)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            float fps = root.get("fps").getAsFloat();
            for (var e : root.getAsJsonObject("clips").entrySet()) {
                JsonObject c = e.getValue().getAsJsonObject();
                Map<String, float[][]> tracks = new HashMap<>();
                for (var t : c.getAsJsonObject("tracks").entrySet()) {
                    JsonObject tr = t.getValue().getAsJsonObject();
                    JsonArray pos = tr.getAsJsonArray("pos"), rot = tr.getAsJsonArray("rot");
                    float[][] data = new float[pos.size()][6];
                    for (int i = 0; i < pos.size(); i++) {
                        JsonArray p = pos.get(i).getAsJsonArray(), r = rot.get(i).getAsJsonArray();
                        for (int k = 0; k < 3; k++) {
                            data[i][k] = p.get(k).getAsFloat();
                            data[i][k + 3] = r.get(k).getAsFloat();
                        }
                    }
                    tracks.put(t.getKey(), data);
                }
                List<Event> events = new ArrayList<>();
                for (JsonElement ev : c.getAsJsonArray("events")) {
                    JsonArray a = ev.getAsJsonArray();
                    events.add(new Event(a.get(0).getAsFloat(), a.get(1).getAsString()));
                }
                out.put(e.getKey(), new Clip(c.get("length").getAsFloat(), c.get("loop").getAsBoolean(), fps, tracks, events));
            }
        } catch (Exception ex) {
            Warpbound.LOG.error("gun_anim {}: {}", model, ex.toString());
        }
        return out;
    }

    static SoundEvent sound(String name) {
        return SoundEvent.createVariableRangeEvent(Warpbound.id("gun." + name));
    }
}
