package dev.warpbound.client.gun;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;

/** Латунная гильза болта: вылетает из окна, крутится, отскакивает от пола со звоном и лежит пару секунд. */
public final class GunCasingParticle extends TextureSheetParticle {
    private boolean clinked;

    private GunCasingParticle(ClientLevel level, double x, double y, double z, double vx, double vy, double vz, SpriteSet sprites) {
        super(level, x, y, z, vx, vy, vz);
        xd = vx;
        yd = vy;
        zd = vz;
        gravity = 0.9f;
        friction = 0.98f;
        quadSize = 0.05f;
        lifetime = 50 + random.nextInt(20);
        pickSprite(sprites);
        roll = random.nextFloat() * 6.28f;
        oRoll = roll;
    }

    @Override
    public void tick() {
        super.tick();
        oRoll = roll;
        if (onGround) {
            xd *= 0.45;
            zd *= 0.45;
            if (!clinked) {
                clinked = true;
                // отскок один раз: дальше гильза лежит
                yd = 0.11;
                level.playLocalSound(x, y, z, SoundEvent.createVariableRangeEvent(ResourceLocation.fromNamespaceAndPath("warpbound", "gun.casing")), SoundSource.PLAYERS,
                        0.35f, 0.9f + random.nextFloat() * 0.25f, false);
            }
        } else {
            roll += 0.7f;
        }
    }

    @Override
    public ParticleRenderType getRenderType() {
        return ParticleRenderType.PARTICLE_SHEET_OPAQUE;
    }

    public record Provider(SpriteSet sprites) implements ParticleProvider<SimpleParticleType> {
        @Override
        public Particle createParticle(SimpleParticleType type, ClientLevel level, double x, double y, double z, double vx, double vy, double vz) {
            return new GunCasingParticle(level, x, y, z, vx, vy, vz, sprites);
        }
    }
}
