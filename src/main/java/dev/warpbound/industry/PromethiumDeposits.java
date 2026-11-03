package dev.warpbound.industry;

import net.minecraft.world.level.ChunkPos;

/**
 * Залежи прометия: хранить нечего, всё считается из сида мира. Мир поделён на квадраты 8×8 чанков, в каждом одно поле 3×3 чанка.
 * Так залежь всегда найдётся недалеко (не больше ~130 блоков), и сервер ничего не сканирует.
 */
public final class PromethiumDeposits {
    /** Сторона квадрата и поля, в чанках. */
    private static final int REGION = 8, FIELD = 3;
    /** Для автотестов: экстрактор качает где угодно. Не сохраняется. */
    public static boolean everywhere;

    private PromethiumDeposits() {
    }

    private static long mix(long seed, long a, long b) {
        long h = seed ^ (a * 341873128712L + b * 132897987541L);
        h = (h ^ (h >>> 30)) * 0xBF58476D1CE4E5B9L;
        h = (h ^ (h >>> 27)) * 0x94D049BB133111EBL;
        return h ^ (h >>> 31);
    }

    /** Левый нижний чанк поля в квадрате. */
    private static ChunkPos fieldOrigin(long seed, int regionX, int regionZ) {
        long h = mix(seed, regionX, regionZ);
        int span = REGION - FIELD + 1;
        return new ChunkPos(regionX * REGION + (int) Math.floorMod(h, (long) span), regionZ * REGION + (int) Math.floorMod(h >>> 16, (long) span));
    }

    public static boolean isDeposit(long seed, int chunkX, int chunkZ) {
        ChunkPos o = fieldOrigin(seed, Math.floorDiv(chunkX, REGION), Math.floorDiv(chunkZ, REGION));
        return chunkX >= o.x && chunkX < o.x + FIELD && chunkZ >= o.z && chunkZ < o.z + FIELD;
    }

    /** Богатство чанка 30–100%; вне залежи 0. */
    public static int richness(long seed, int chunkX, int chunkZ) {
        if (!isDeposit(seed, chunkX, chunkZ)) return everywhere ? 100 : 0;
        return 30 + (int) Math.floorMod(mix(seed + 1, chunkX, chunkZ), 71L);
    }

    /** Центральный чанк ближайшего поля: в нём лежит большой выход битума. */
    public static ChunkPos nearestField(long seed, int chunkX, int chunkZ) {
        int rx = Math.floorDiv(chunkX, REGION), rz = Math.floorDiv(chunkZ, REGION);
        ChunkPos best = null;
        long bestDist = Long.MAX_VALUE;
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                ChunkPos o = fieldOrigin(seed, rx + dx, rz + dz);
                ChunkPos c = new ChunkPos(o.x + FIELD / 2, o.z + FIELD / 2);
                long d = (long) (c.x - chunkX) * (c.x - chunkX) + (long) (c.z - chunkZ) * (c.z - chunkZ);
                if (d < bestDist) {
                    bestDist = d;
                    best = c;
                }
            }
        }
        return best;
    }

    /** Ближайшее поле, подходящее под условие (например, не под водой): идём по кольцам квадратов. Не нашлось — самое ближнее. */
    public static ChunkPos nearestField(long seed, int chunkX, int chunkZ, java.util.function.Predicate<ChunkPos> fits) {
        int rx = Math.floorDiv(chunkX, REGION), rz = Math.floorDiv(chunkZ, REGION);
        ChunkPos best = null;
        long bestDist = Long.MAX_VALUE;
        for (int ring = 0; ring <= 16; ring++) {
            for (int dx = -ring; dx <= ring; dx++) {
                for (int dz = -ring; dz <= ring; dz++) {
                    if (Math.max(Math.abs(dx), Math.abs(dz)) != ring) continue;
                    ChunkPos o = fieldOrigin(seed, rx + dx, rz + dz);
                    ChunkPos c = new ChunkPos(o.x + FIELD / 2, o.z + FIELD / 2);
                    if (!fits.test(c)) continue;
                    long d = (long) (c.x - chunkX) * (c.x - chunkX) + (long) (c.z - chunkZ) * (c.z - chunkZ);
                    if (d < bestDist) {
                        bestDist = d;
                        best = c;
                    }
                }
            }
            if (best != null) return best;
        }
        return nearestField(seed, chunkX, chunkZ);
    }

    public static boolean isFieldCenter(long seed, int chunkX, int chunkZ) {
        ChunkPos o = fieldOrigin(seed, Math.floorDiv(chunkX, REGION), Math.floorDiv(chunkZ, REGION));
        return chunkX == o.x + FIELD / 2 && chunkZ == o.z + FIELD / 2;
    }
}
