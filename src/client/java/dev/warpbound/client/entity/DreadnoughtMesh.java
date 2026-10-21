package dev.warpbound.client.entity;

import dev.warpbound.Warpbound;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

/**
 * Геометрия дредноута лежит в assets/warpbound/models/entity/dreadnought.json
 * (генерирует tools/dreadnought/gen.py). Здесь только запасной скелет без кубов,
 * чтобы с битым файлом игра не падала, а дредноут был просто невидим.
 */
public final class DreadnoughtMesh {
    private DreadnoughtMesh() {
    }

    public static LayerDefinition create() {
        LayerDefinition loaded = JsonMesh.load(Warpbound.id("models/entity/dreadnought.json"));
        return loaded != null ? loaded : skeleton();
    }

    private static LayerDefinition skeleton() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition body = empty(mesh.getRoot(), "body");
        for (String side : new String[]{"r", "l"}) {
            empty(empty(empty(body, "leg_" + side), "shin_" + side), "foot_" + side);
        }
        PartDefinition torso = empty(empty(body, "waist"), "torso");
        empty(torso, "head");
        empty(empty(torso, "arm_r"), "gun");
        empty(empty(torso, "arm_l"), "fist");
        return LayerDefinition.create(mesh, 16, 16);
    }

    private static PartDefinition empty(PartDefinition parent, String name) {
        return parent.addOrReplaceChild(name, CubeListBuilder.create(), PartPose.ZERO);
    }
}
