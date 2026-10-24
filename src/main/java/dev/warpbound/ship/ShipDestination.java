package dev.warpbound.ship;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import dev.warpbound.core.DataRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;

import java.util.Optional;

/**
 * Пункт назначения из data/&lt;ns&gt;/ship_destination/*.json: мир, на орбиту которого выходит корабль,
 * и куда телепортариум высаживает экипаж. Мир, которого нет на сервере, на навигационном столе не показывается.
 */
public record ShipDestination(String name, ResourceLocation dimension, String landing, int x, int z, int radius) {
    public static final Codec<ShipDestination> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.STRING.fieldOf("name").forGetter(ShipDestination::name),
            ResourceLocation.CODEC.fieldOf("dimension").forGetter(ShipDestination::dimension),
            Codec.STRING.optionalFieldOf("landing", "spawn").forGetter(ShipDestination::landing),
            Codec.INT.optionalFieldOf("x", 0).forGetter(ShipDestination::x),
            Codec.INT.optionalFieldOf("z", 0).forGetter(ShipDestination::z),
            Codec.INT.optionalFieldOf("radius", 48).forGetter(ShipDestination::radius)
    ).apply(i, ShipDestination::new));

    public static final DataRegistry<ShipDestination> REGISTRY = new DataRegistry<>("ship_destination", CODEC);

    /** Родной мир: на его орбите корабль появляется после старта с верфи. */
    public static final ResourceLocation HOME = dev.warpbound.Warpbound.id("overworld");

    public static void register() {
    }

    public Optional<ServerLevel> level(MinecraftServer server) {
        return Optional.ofNullable(server.getLevel(ResourceKey.create(Registries.DIMENSION, dimension)));
    }

    /**
     * Точка высадки. «dock» — туда, где корабль поднялся (у верфи), «spawn» — точка появления мира,
     * «surface» — случайная твёрдая поверхность в радиусе от (x, z).
     */
    public BlockPos landingPos(ServerLevel level, Ship ship, RandomSource random) {
        if (landing.equals("dock") && ship.dockDimension != null && ship.dockDimension.equals(dimension)) {
            return BlockPos.containing(ship.dockX, ship.dockY, ship.dockZ);
        }
        if (landing.equals("surface")) {
            int px = x + random.nextInt(radius * 2 + 1) - radius;
            int pz = z + random.nextInt(radius * 2 + 1) - radius;
            level.getChunk(px >> 4, pz >> 4);
            return level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, new BlockPos(px, 0, pz));
        }
        BlockPos spawn = level.getSharedSpawnPos();
        return level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, spawn);
    }

    public boolean isLevel(Level level) {
        return level.dimension().location().equals(dimension);
    }
}
