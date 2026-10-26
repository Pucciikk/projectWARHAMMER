package dev.warpbound.core;

import dev.warpbound.Warpbound;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.sounds.SoundEvent;

/**
 * Звуки мода. Файлы — в assets/warpbound/sounds.json: пока это ванильные звуки с другой высотой тона,
 * свой .ogg подменяет запись без правок кода.
 */
public final class WarpboundSounds {
    public static final SoundEvent SHUTTLE_ENGINE = register("shuttle.engine");
    public static final SoundEvent SHUTTLE_ROAR = register("shuttle.roar");
    public static final SoundEvent SHUTTLE_TOUCHDOWN = register("shuttle.touchdown");
    public static final SoundEvent CAPSULE_RELEASE = register("capsule.release");
    public static final SoundEvent CAPSULE_THRUST = register("capsule.thrust");
    public static final SoundEvent CAPSULE_OPEN = register("capsule.open");
    public static final SoundEvent WARP_RITUAL = register("warp.ritual");
    public static final SoundEvent WARP_FLAME = register("warp.flame");
    public static final SoundEvent WARP_WHISPER = register("warp.whisper");
    public static final SoundEvent WARP_BURST = register("warp.burst");
    public static final SoundEvent PRIEST_STEP = register("priest.step");
    public static final SoundEvent PRIEST_SERVO = register("priest.servo");
    public static final SoundEvent PRIEST_AMBIENT = register("priest.ambient");
    public static final SoundEvent PRIEST_HURT = register("priest.hurt");
    public static final SoundEvent DARK_PRIEST_STEP = register("dark_priest.step");
    public static final SoundEvent DARK_PRIEST_FLESH = register("dark_priest.flesh");
    public static final SoundEvent DARK_PRIEST_SERVO = register("dark_priest.servo");
    public static final SoundEvent DARK_PRIEST_AMBIENT = register("dark_priest.ambient");
    public static final SoundEvent DARK_PRIEST_HURT = register("dark_priest.hurt");

    private WarpboundSounds() {
    }

    private static SoundEvent register(String name) {
        return Registry.register(BuiltInRegistries.SOUND_EVENT, Warpbound.id(name), SoundEvent.createVariableRangeEvent(Warpbound.id(name)));
    }

    /** Вызывается из Warpbound.onInitialize, чтобы класс загрузился до заморозки реестров. */
    public static void register() {
    }
}
