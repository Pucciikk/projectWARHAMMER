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

/** Руна Тёмного Языка или знак бога: проступает, медленно всплывает, мерцает и тает. */
public class WarpRuneParticle extends TextureSheetParticle {
    private final float baseSize;
    private final float phase;

    protected WarpRuneParticle(ClientLevel level, double x, double y, double z, double dx, double dy, double dz, SpriteSet sprites) {
        super(level, x, y, z, dx, dy, dz);
        this.xd = dx;
        this.yd = dy;
        this.zd = dz;
        this.friction = 0.96f;
        this.gravity = 0;
        this.hasPhysics = false;
        this.lifetime = 40 + random.nextInt(40);
        this.baseSize = 0.18f + random.nextFloat() * 0.14f;
        this.quadSize = 0;
        this.phase = random.nextFloat() * 6.28f;
        pickSprite(sprites);
    }

    @Override
    public void tick() {
        super.tick();
        if (removed) return;
        float t = (float) age / lifetime;
        quadSize = baseSize * Math.min(1f, t * 6f);
        float flicker = 0.75f + 0.25f * Mth.sin(age * 1.3f + phase);
        alpha = (t < 0.75f ? 1f : 1f - (t - 0.75f) / 0.25f) * flicker;
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
            return new WarpRuneParticle(level, x, y, z, dx, dy, dz, sprites);
        }
    }
}
