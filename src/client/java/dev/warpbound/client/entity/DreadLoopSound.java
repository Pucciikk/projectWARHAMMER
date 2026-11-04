package dev.warpbound.client.entity;

import dev.warpbound.Warpbound;
import dev.warpbound.entity.dreadnought.concept.DreadConceptEntity;
import net.minecraft.client.resources.sounds.AbstractTickableSoundInstance;
import net.minecraft.client.resources.sounds.SoundInstance;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;

/** Негромкий гул дредноута: идёт за машиной и глохнет со смертью. */
final class DreadLoopSound extends AbstractTickableSoundInstance {
    private final DreadConceptEntity entity;

    DreadLoopSound(DreadConceptEntity entity) {
        super(SoundEvent.createVariableRangeEvent(Warpbound.id("dread.idle")), SoundSource.HOSTILE, SoundInstance.createUnseededRandom());
        this.entity = entity;
        looping = true;
        delay = 0;
        volume = 0.35f;
        x = entity.getX();
        y = entity.getY() + 2;
        z = entity.getZ();
    }

    @Override
    public void tick() {
        if (entity.isRemoved() || !entity.isAlive() || !entity.isVehicle() || entity.fuel() <= 0) {
            stop();
            return;
        }
        x = entity.getX();
        y = entity.getY() + 2;
        z = entity.getZ();
    }
}
