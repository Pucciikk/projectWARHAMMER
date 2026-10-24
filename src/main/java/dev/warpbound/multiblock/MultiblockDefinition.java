package dev.warpbound.multiblock;

import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Predicate;

/**
 * Шаблон мультиблока из data/&lt;ns&gt;/multiblock/*.json.
 * <p>
 * layers — слои снизу вверх; в слое строки идут по Z (от переда к заду), символы — по X (слева направо).
 * Шаблон описан для ядра, которое смотрит на север: «перед» машины — сторона -Z.
 * key — что означает символ: id блока или #тег. Пробел — «что угодно», точка — «воздух».
 * Символ core встречается ровно один раз и обозначает ядро.
 */
public record MultiblockDefinition(String name, List<List<String>> layers, Map<String, String> key, String core,
                                   boolean mirrorable) {
    public static final Codec<MultiblockDefinition> CODEC = RecordCodecBuilder.<MultiblockDefinition>create(i -> i.group(
            Codec.STRING.fieldOf("name").forGetter(MultiblockDefinition::name),
            Codec.STRING.listOf().listOf().fieldOf("layers").forGetter(MultiblockDefinition::layers),
            Codec.unboundedMap(Codec.STRING, Codec.STRING).fieldOf("key").forGetter(MultiblockDefinition::key),
            Codec.STRING.optionalFieldOf("core", "C").forGetter(MultiblockDefinition::core),
            Codec.BOOL.optionalFieldOf("mirrorable", false).forGetter(MultiblockDefinition::mirrorable)
    ).apply(i, MultiblockDefinition::new)).validate(MultiblockDefinition::check);

    /**
     * Одна клетка шаблона: смещение от ядра (ядро смотрит на север), что там должно стоять
     * и какой блок ставить при автопостановке (для тега — первый блок из него).
     */
    public record Cell(BlockPos offset, Predicate<BlockState> matches, Component expected, BlockState place) {
    }

    private static DataResult<MultiblockDefinition> check(MultiblockDefinition def) {
        int cores = 0;
        for (List<String> layer : def.layers) for (String row : layer) for (char c : row.toCharArray()) {
            if (String.valueOf(c).equals(def.core)) cores++;
            else if (c != ' ' && c != '.' && !def.key.containsKey(String.valueOf(c))) {
                return DataResult.error(() -> "символ '" + c + "' не описан в key");
            }
        }
        if (cores != 1) {
            int n = cores;
            return DataResult.error(() -> "ядро '" + def.core + "' должно встречаться ровно один раз, а не " + n);
        }
        return DataResult.success(def);
    }

    /** Все клетки, кроме ядра и «что угодно», со смещениями относительно ядра. */
    public List<Cell> cells() {
        BlockPos corePos = findCore();
        Map<String, Cell> cache = new HashMap<>();
        List<Cell> cells = new ArrayList<>();
        for (int y = 0; y < layers.size(); y++) {
            List<String> layer = layers.get(y);
            for (int z = 0; z < layer.size(); z++) {
                String row = layer.get(z);
                for (int x = 0; x < row.length(); x++) {
                    String symbol = String.valueOf(row.charAt(x));
                    if (symbol.equals(" ") || symbol.equals(core)) continue;
                    BlockPos offset = new BlockPos(x, y, z).subtract(corePos);
                    Cell proto = cache.computeIfAbsent(symbol, this::cellFor);
                    cells.add(new Cell(offset, proto.matches, proto.expected, proto.place));
                }
            }
        }
        return cells;
    }

    private BlockPos findCore() {
        for (int y = 0; y < layers.size(); y++) {
            List<String> layer = layers.get(y);
            for (int z = 0; z < layer.size(); z++) {
                int x = layer.get(z).indexOf(core);
                if (x >= 0) return new BlockPos(x, y, z);
            }
        }
        throw new IllegalStateException("нет ядра"); // не случится: проверено кодеком
    }

    private Cell cellFor(String symbol) {
        if (symbol.equals(".")) {
            return new Cell(BlockPos.ZERO, BlockState::isAir, Component.translatable("multiblock.warpbound.air"),
                    Blocks.AIR.defaultBlockState());
        }
        String ref = key.get(symbol);
        if (ref.startsWith("#")) {
            TagKey<Block> tag = TagKey.create(Registries.BLOCK, ResourceLocation.parse(ref.substring(1)));
            BlockState first = BuiltInRegistries.BLOCK.getTag(tag)
                    .flatMap(set -> set.stream().findFirst())
                    .map(h -> h.value().defaultBlockState())
                    .orElse(Blocks.AIR.defaultBlockState());
            return new Cell(BlockPos.ZERO, s -> s.is(tag), Component.literal(ref), first);
        }
        Block block = BuiltInRegistries.BLOCK.get(ResourceLocation.parse(ref));
        if (block == Blocks.AIR) {
            // Неизвестный блок — клетку нельзя собрать, но игра не падает
            return new Cell(BlockPos.ZERO, s -> false, Component.literal("?" + ref), Blocks.AIR.defaultBlockState());
        }
        return new Cell(BlockPos.ZERO, s -> s.is(block), block.getName(), block.defaultBlockState());
    }
}
