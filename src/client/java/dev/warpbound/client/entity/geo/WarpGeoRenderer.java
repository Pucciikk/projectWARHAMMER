package dev.warpbound.client.entity.geo;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.util.Mth;
import dev.warpbound.Warpbound;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import software.bernie.geckolib.animatable.GeoAnimatable;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.function.ToDoubleBiFunction;

/**
 * Рендер любой модели GeckoLib мода: geo/entity/&lt;model&gt;.geo.json, animations/entity/&lt;model&gt;.animation.json,
 * textures/entity/&lt;текстура&gt;.png и светящаяся &lt;текстура&gt;_glow.png поверх.
 * <p>
 * Варианты (культисты, легионы, фазы босса) — одна геометрия: своя текстура и набор скрытых костей.
 */
public class WarpGeoRenderer<T extends Entity & GeoAnimatable> extends GeoEntityRenderer<T> {
    private final Map<String, ResourceLocation> textures = new HashMap<>();
    private Function<T, String> texture;
    private Collection<String> toggledBones = List.of();
    private Function<T, Set<String>> hiddenBones = e -> Set.of();
    private ToDoubleBiFunction<T, Float> scale = (e, partialTick) -> 1.0;
    private boolean vehicle;

    /** Модель с костью головы {@code head}: она поворачивается за взглядом. */
    public WarpGeoRenderer(EntityRendererProvider.Context context, String model) {
        this(context, model, "head");
    }

    public WarpGeoRenderer(EntityRendererProvider.Context context, String model, String headBone) {
        super(context, new DefaultedEntityGeoModel<>(Warpbound.id(model), headBone));
        this.texture = e -> model;
        addRenderLayer(new GlowLayer<>(this));
    }

    /** Текстура по сущности (имя файла без .png). */
    public WarpGeoRenderer<T> texture(Function<T, String> texture) {
        this.texture = texture;
        return this;
    }

    /** Кости, которые включаются и выключаются по сущности: всё из {@code toggled}, что не вернул {@code hidden}, видно. */
    public WarpGeoRenderer<T> bones(Collection<String> toggled, Function<T, Set<String>> hidden) {
        this.toggledBones = toggled;
        this.hiddenBones = hidden;
        return this;
    }

    /** Размер модели, может меняться на ходу (рост демона из жреца). */
    public WarpGeoRenderer<T> scale(ToDoubleBiFunction<T, Float> scale) {
        this.scale = scale;
        return this;
    }

    /**
     * Не живая сущность (челнок, капсула, разлом): GeckoLib поворачивает по курсу только живых,
     * здесь курс и тангаж берутся из yRot/xRot сущности; тангаж — вокруг середины высоты.
     */
    public WarpGeoRenderer<T> vehicle() {
        this.vehicle = true;
        return this;
    }

    public WarpGeoRenderer<T> shadow(float radius) {
        this.shadowRadius = radius;
        return this;
    }

    @Override
    public ResourceLocation getTextureLocation(T entity) {
        return textures.computeIfAbsent(texture.apply(entity), name -> Warpbound.id("textures/entity/" + name + ".png"));
    }

    @Override
    public void preRender(PoseStack poseStack, T entity, BakedGeoModel model, net.minecraft.client.renderer.MultiBufferSource bufferSource,
                          com.mojang.blaze3d.vertex.VertexConsumer buffer, boolean isReRender, float partialTick,
                          int packedLight, int packedOverlay, int colour) {
        // модель одна на все сущности типа — видимость костей выставляем перед каждой отрисовкой
        if (!isReRender && !toggledBones.isEmpty()) {
            Set<String> hidden = hiddenBones.apply(entity);
            for (String name : toggledBones) model.getBone(name).ifPresent(bone -> bone.setHidden(hidden.contains(name)));
        }
        super.preRender(poseStack, entity, model, bufferSource, buffer, isReRender, partialTick, packedLight, packedOverlay, colour);
    }

    @Override
    protected void applyRotations(T entity, PoseStack poseStack, float ageInTicks, float rotationYaw, float partialTick, float nativeScale) {
        if (!vehicle) {
            super.applyRotations(entity, poseStack, ageInTicks, rotationYaw, partialTick, nativeScale);
            return;
        }
        poseStack.mulPose(Axis.YP.rotationDegrees(180f - Mth.rotLerp(partialTick, entity.yRotO, entity.getYRot())));
        float pitch = Mth.lerp(partialTick, entity.xRotO, entity.getXRot());
        if (pitch != 0) {
            float mid = entity.getBbHeight() / 2;
            poseStack.translate(0, mid, 0);
            poseStack.mulPose(Axis.XP.rotationDegrees(-pitch));
            poseStack.translate(0, -mid, 0);
        }
    }

    @Override
    public void scaleModelForRender(float widthScale, float heightScale, PoseStack poseStack, T entity, BakedGeoModel model,
                                    boolean isReRender, float partialTick, int packedLight, int packedOverlay) {
        float s = (float) scale.applyAsDouble(entity, partialTick);
        super.scaleModelForRender(widthScale * s, heightScale * s, poseStack, entity, model, isReRender, partialTick,
                packedLight, packedOverlay);
    }
}
