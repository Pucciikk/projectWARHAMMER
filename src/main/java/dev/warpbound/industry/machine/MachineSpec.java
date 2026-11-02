package dev.warpbound.industry.machine;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;

import java.util.List;

/**
 * Описание машины цепочки из data/warpbound/machine_spec: сколько слотов и баков, энергия, порты.
 * kind: processor — рецепты; generator — жжёт топливо; source — сама даёт жидкость; custom — логика в своём классе.
 */
public record MachineSpec(String kind, int energyUse, int energyOutput, int slotsIn, int slotsOut, int tanksIn, int tanksOut,
                          String sourceFluid, int sourceRateMb, List<Port> ports) {
    public static final Codec<MachineSpec> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.STRING.fieldOf("kind").forGetter(MachineSpec::kind),
            Codec.INT.optionalFieldOf("energy_use", 0).forGetter(MachineSpec::energyUse),
            Codec.INT.optionalFieldOf("energy_output", 0).forGetter(MachineSpec::energyOutput),
            Codec.INT.optionalFieldOf("slots_in", 0).forGetter(MachineSpec::slotsIn),
            Codec.INT.optionalFieldOf("slots_out", 0).forGetter(MachineSpec::slotsOut),
            Codec.INT.optionalFieldOf("tanks_in", 0).forGetter(MachineSpec::tanksIn),
            Codec.INT.optionalFieldOf("tanks_out", 0).forGetter(MachineSpec::tanksOut),
            Codec.STRING.optionalFieldOf("source_fluid", "").forGetter(MachineSpec::sourceFluid),
            Codec.INT.optionalFieldOf("source_rate_mb", 0).forGetter(MachineSpec::sourceRateMb),
            Port.CODEC.listOf().optionalFieldOf("ports", List.of()).forGetter(MachineSpec::ports)
    ).apply(i, MachineSpec::new));

    /** Разъём на цоколе: смещение от ядра при взгляде машины на север и грань, куда он смотрит. */
    public record Port(Kind kind, boolean output, BlockPos offset, Direction face) {
        public static final Codec<Port> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.STRING.xmap(Kind::parse, k -> k.name().toLowerCase(java.util.Locale.ROOT)).fieldOf("kind").forGetter(Port::kind),
                Codec.BOOL.fieldOf("output").forGetter(Port::output),
                Codec.INT.fieldOf("x").forGetter(p -> p.offset().getX()),
                Codec.INT.fieldOf("y").forGetter(p -> p.offset().getY()),
                Codec.INT.fieldOf("z").forGetter(p -> p.offset().getZ()),
                Direction.CODEC.fieldOf("face").forGetter(Port::face)
        ).apply(i, (kind, output, x, y, z, face) -> new Port(kind, output, new BlockPos(x, y, z), face)));
    }

    public enum Kind {
        ITEM, FLUID, ENERGY;

        static Kind parse(String s) {
            return valueOf(s.toUpperCase(java.util.Locale.ROOT));
        }
    }
}
