package dev.warpbound.client.entity;

import dev.warpbound.core.WarpboundSounds;
import dev.warpbound.entity.transport.ShuttleEntity;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientEntityEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.sounds.AbstractTickableSoundInstance;
import net.minecraft.client.resources.sounds.SoundInstance;
import net.minecraft.sounds.SoundSource;

/** Гул двигателей челнока: петля следует за ним, громче на вертикальной тяге, стихает, когда он улетает. */
public final class ShuttleSounds {
    private ShuttleSounds() {
    }

    public static void register() {
        ClientEntityEvents.ENTITY_LOAD.register((entity, world) -> {
            if (entity instanceof ShuttleEntity shuttle) Minecraft.getInstance().getSoundManager().play(new Engine(shuttle));
        });
    }

    private static final class Engine extends AbstractTickableSoundInstance {
        private final ShuttleEntity shuttle;

        Engine(ShuttleEntity shuttle) {
            super(WarpboundSounds.SHUTTLE_ENGINE, SoundSource.NEUTRAL, SoundInstance.createUnseededRandom());
            this.shuttle = shuttle;
            this.looping = true;
            this.delay = 0;
            this.volume = 0.01f;
            this.x = shuttle.getX();
            this.y = shuttle.getY();
            this.z = shuttle.getZ();
        }

        @Override
        public void tick() {
            if (shuttle.isRemoved()) {
                stop();
                return;
            }
            x = shuttle.getX();
            y = shuttle.getY() + 3;
            z = shuttle.getZ();
            boolean vertical = shuttle.phase() == ShuttleEntity.Phase.DESCEND || shuttle.phase() == ShuttleEntity.Phase.PARKED;
            float want = vertical ? 2.6f : 2.0f;
            volume += (want - volume) * 0.08f;
            pitch = vertical ? 0.85f : 1.0f;
        }
    }
}
