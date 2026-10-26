package dev.warpbound.client.particle;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;

/**
 * Язык синего варп-пламени: светится в темноте, кадры анимации сменяются с возрастом,
 * пламя разгорается, тянется вверх и гаснет. Скорость задаёт направление выброса.
 */
public class WarpFlameParticle extends TextureSheetParticle {
    private final SpriteSet sprites;
    private final float baseSize;

    protected WarpFlameParticle(ClientLevel level, double x, double y, double z, double dx, double dy, double dz, SpriteSet sprites) {
        super(level, x, y, z, dx, dy, dz);
        this.sprites = sprites;
        this.xd = dx;
        this.yd = dy;
        this.zd = dz;
        this.friction = 0.9f;
        this.gravity = -0.04f;               // пламя тянет вверх
        this.hasPhysics = false;
        this.lifetime = 12 + random.nextInt(12);
        this.baseSize = 0.28f + random.nextFloat() * 0.35f;
        this.quadSize = baseSize;
        this.roll = this.oRoll = (random.nextFloat() - 0.5f) * 0.4f;
        setSpriteFromAge(sprites);
    }

    @Override
    public void tick() {
        super.tick();
        if (removed) return;
        setSpriteFromAge(sprites);
        float t = (float) age / lifetime;
        quadSize = baseSize * (t < 0.2f ? 0.6f + t * 2 : 1f - (t - 0.2f) * 0.7f);
        alpha = t < 0.7f ? 1f : 1f - (t - 0.7f) / 0.3f;
        oRoll = roll;
        roll += Mth.sin(age * 0.6f) * 0.03f;
    }

    @Override
    public ParticleRenderType getRenderType() {
        return ParticleRenderType.PARTICLE_SHEET_TRANSLUCENT;
    }

    @Override
    protected int getLightColor(float partialTick) {
        return LightTexture.FULL_BRIGHT;
    }

    public record Provider(SpriteSet sprites) implements ParticleProvider<SimpleParticleType> {
        @Override
        public Particle createParticle(SimpleParticleType type, ClientLevel level, double x, double y, double z,
                                       double dx, double dy, double dz) {
            return new WarpFlameParticle(level, x, y, z, dx, dy, dz, sprites);
        }
    }
}
