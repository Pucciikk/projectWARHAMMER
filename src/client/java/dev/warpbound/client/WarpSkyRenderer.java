package dev.warpbound.client;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.BufferUploader;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexFormat;
import dev.warpbound.Warpbound;
import dev.warpbound.ship.ShipInteriors;
import net.fabricmc.fabric.api.client.rendering.v1.CoreShaderRegistrationCallback;
import net.fabricmc.fabric.api.client.rendering.v1.DimensionRenderingRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderContext;
import net.minecraft.client.renderer.ShaderInstance;
import net.minecraft.util.RandomSource;
import org.joml.Matrix4f;

/**
 * Небо измерения корабля: один полноэкранный проход шейдера warp_sky.
 * Шейдер сам переводит направление взгляда в координаты «туннеля», поэтому небо
 * поворачивается вместе с камерой, а нос корабля всегда смотрит в центр варпа.
 */
public final class WarpSkyRenderer {
    private static ShaderInstance shader;
    private static final RandomSource RANDOM = RandomSource.create();

    private static float time;
    private static float flash;
    private static float boltSeed = 1f;

    private WarpSkyRenderer() {
    }

    static void register() {
        CoreShaderRegistrationCallback.EVENT.register(context ->
                context.register(Warpbound.id("warp_sky"), DefaultVertexFormat.POSITION, loaded -> shader = loaded));
        DimensionRenderingRegistry.registerDimensionEffects(Warpbound.id("ship_interior"), new ShipInteriorEffects());
        DimensionRenderingRegistry.registerSkyRenderer(ShipInteriors.LEVEL_KEY, WarpSkyRenderer::render);
    }

    /** Вспышка большой молнии. Позже её будут вызывать варп-события. */
    public static void strike() {
        flash = 1f;
        boltSeed = RANDOM.nextInt(1000);
    }

    private static void render(WorldRenderContext context) {
        if (shader == null) return;

        float dt = ClientShipState.advanceFrame();
        float field = ClientShipState.field();
        float storm = ClientShipState.storm();
        float enter = ClientShipState.enter();
        time = (time + dt) % 600f;

        // Большие молнии бьют сами: чаще в шторм и при слабом Поле (как в прототипе)
        if (enter > 0.95f) {
            float rate = 0.05f + 0.5f * storm + 0.35f * (1f - field);
            if (RANDOM.nextFloat() < rate * dt) {
                flash = 0.7f + 0.3f * RANDOM.nextFloat();
                boltSeed = RANDOM.nextInt(1000);
            }
        }
        flash *= (float) Math.exp(-dt * 3.5);

        // Только поворот камеры: перенос в положении неба не участвует
        Matrix4f invViewProj = new Matrix4f(context.projectionMatrix()).mul(context.positionMatrix()).invert();
        float eased = enter * enter * (3f - 2f * enter);

        shader.safeGetUniform("InvViewProj").set(invViewProj);
        shader.safeGetUniform("uTime").set(time);
        shader.safeGetUniform("uField").set(field);
        shader.safeGetUniform("uStorm").set(storm);
        shader.safeGetUniform("uCorr").set(ClientChaosState.get().corruption() / 100f);
        shader.safeGetUniform("uEnter").set(eased);
        shader.safeGetUniform("uFlash").set(flash);
        shader.safeGetUniform("uSpeed").set(0.75f);
        shader.safeGetUniform("uBoltSeed").set(boltSeed);

        RenderSystem.setShader(() -> shader);
        RenderSystem.depthMask(false);
        RenderSystem.disableDepthTest();
        RenderSystem.disableBlend();
        RenderSystem.disableCull();

        BufferBuilder buffer = Tesselator.getInstance().begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION);
        buffer.addVertex(-1f, -1f, 0f);
        buffer.addVertex(1f, -1f, 0f);
        buffer.addVertex(1f, 1f, 0f);
        buffer.addVertex(-1f, 1f, 0f);
        BufferUploader.drawWithShader(buffer.buildOrThrow());

        RenderSystem.enableCull();
        RenderSystem.enableDepthTest();
        RenderSystem.depthMask(true);
    }
}
