package dev.warpbound.client.ship;

import dev.warpbound.client.ClientShipState;
import dev.warpbound.core.WarpboundSounds;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.resources.sounds.AbstractTickableSoundInstance;
import net.minecraft.client.resources.sounds.SoundInstance;
import net.minecraft.sounds.SoundSource;

/** Гул двигателей на борту: петля у игрока, громкость и тон растут с ходом корабля, гаснет при остановке. */
public final class ShipEngineSound extends AbstractTickableSoundInstance {
    private static ShipEngineSound playing;

    private ShipEngineSound() {
        super(WarpboundSounds.SHUTTLE_ENGINE, SoundSource.AMBIENT, SoundInstance.createUnseededRandom());
        this.looping = true;
        this.delay = 0;
        this.volume = 0.01f;
        this.relative = true;   // звук «везде» на корабле, а не в точке
    }

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(mc -> {
            boolean want = ClientShipState.enginesOn() || ClientShipState.cruise() > 0.05f;
            if (want && (playing == null || playing.isStopped())) {
                playing = new ShipEngineSound();
                mc.getSoundManager().play(playing);
            }
        });
    }

    @Override
    public void tick() {
        float cruise = ClientShipState.cruise();
        if (!ClientShipState.aboard() || cruise < 0.02f && !ClientShipState.enginesOn()) {
            stop();
            return;
        }
        float target = 0.25f + 0.55f * cruise;
        volume += (target - volume) * 0.05f;
        pitch = 0.5f + 0.25f * cruise;
    }
}
