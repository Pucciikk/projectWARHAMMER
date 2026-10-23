package dev.warpbound.client.entity;

import dev.warpbound.Warpbound;
import dev.warpbound.operator.TechPriestEntity;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.layers.EyesLayer;
import net.minecraft.resources.ResourceLocation;

/** Техножрец на гуманоидной модели игрока, со светящейся оптикой поверх. */
public class TechPriestRenderer extends HumanoidMobRenderer<TechPriestEntity, HumanoidModel<TechPriestEntity>> {
    private final ResourceLocation texture;

    public TechPriestRenderer(EntityRendererProvider.Context context, String name) {
        super(context, new HumanoidModel<>(context.bakeLayer(ModelLayers.PLAYER)), 0.5f);
        this.texture = Warpbound.id("textures/entity/" + name + ".png");
        RenderType eyes = RenderType.eyes(Warpbound.id("textures/entity/" + name + "_eyes.png"));
        addLayer(new EyesLayer<>(this) {
            @Override
            public RenderType renderType() {
                return eyes;
            }
        });
    }

    @Override
    public ResourceLocation getTextureLocation(TechPriestEntity entity) {
        return texture;
    }
}
