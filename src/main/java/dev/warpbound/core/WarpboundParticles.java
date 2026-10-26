package dev.warpbound.core;

import dev.warpbound.Warpbound;
import net.fabricmc.fabric.api.particle.v1.FabricParticleTypes;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;

/** Свои частицы: мягкое синее варп-пламя и парящие руны. Спрайты — tools/models/warp_rift.py. */
public final class WarpboundParticles {
    public static final SimpleParticleType WARP_FLAME = register("warp_flame");
    public static final SimpleParticleType WARP_RUNE = register("warp_rune");

    private WarpboundParticles() {
    }

    private static SimpleParticleType register(String name) {
        return Registry.register(BuiltInRegistries.PARTICLE_TYPE, Warpbound.id(name), FabricParticleTypes.simple(true));
    }

    public static void register() {
    }
}
