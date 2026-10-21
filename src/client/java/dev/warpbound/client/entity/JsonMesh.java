package dev.warpbound.client.entity;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.warpbound.Warpbound;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.resources.Resource;

import java.io.Reader;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * Модель сущности из JSON в ресурсах (его пишет tools/dreadnought/gen.py).
 * Читается при каждой перезагрузке ресурсов, поэтому F3+T подхватывает правки без перезапуска игры.
 */
public final class JsonMesh {
    private JsonMesh() {
    }

    /** null, если файла нет или он битый. */
    public static LayerDefinition load(ResourceLocation id) {
        Optional<Resource> resource = Minecraft.getInstance().getResourceManager().getResource(id);
        if (resource.isEmpty()) {
            Warpbound.LOG.error("Нет модели {}", id);
            return null;
        }
        try (Reader reader = resource.get().openAsReader()) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            MeshDefinition mesh = new MeshDefinition();
            Map<String, PartDefinition> parts = new HashMap<>();
            parts.put("root", mesh.getRoot());
            for (JsonElement el : root.getAsJsonArray("parts")) {
                JsonObject p = el.getAsJsonObject();
                CubeListBuilder cubes = CubeListBuilder.create();
                for (JsonElement ce : p.getAsJsonArray("cubes")) {
                    JsonObject c = ce.getAsJsonObject();
                    float[] uv = floats(c.getAsJsonArray("uv"));
                    float[] from = floats(c.getAsJsonArray("from"));
                    float[] size = floats(c.getAsJsonArray("size"));
                    cubes.texOffs((int) uv[0], (int) uv[1]).addBox(from[0], from[1], from[2], size[0], size[1], size[2]);
                }
                float[] o = floats(p.getAsJsonArray("offset"));
                float[] r = floats(p.getAsJsonArray("rotation"));
                PartDefinition parent = parts.get(p.get("parent").getAsString());
                String name = p.get("name").getAsString();
                parts.put(name, parent.addOrReplaceChild(name, cubes, PartPose.offsetAndRotation(o[0], o[1], o[2], r[0], r[1], r[2])));
            }
            JsonArray tex = root.getAsJsonArray("texture");
            return LayerDefinition.create(mesh, tex.get(0).getAsInt(), tex.get(1).getAsInt());
        } catch (Exception e) {
            Warpbound.LOG.error("Не удалось прочитать модель {}", id, e);
            return null;
        }
    }

    private static float[] floats(JsonArray array) {
        float[] out = new float[array.size()];
        for (int i = 0; i < out.length; i++) {
            out[i] = array.get(i).getAsFloat();
        }
        return out;
    }
}
