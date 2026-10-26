package dev.warpbound.multiblock;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.properties.BooleanProperty;

import java.util.List;

/**
 * Машина-мультиблок: блок-сущность ядра, у которой есть {@link MultiblockController}.
 * Отдельный интерфейс, а не базовый класс: ядром может быть и печь (горн обломков), и своя машина.
 */
public interface MultiblockHost {
    /** Свойство ядра «машина собрана»: собранное ядро прячет свою модель, рисуется цельная машина. */
    BooleanProperty FORMED = BooleanProperty.create("formed");

    MultiblockController multiblock();

    default boolean isFormed() {
        return multiblock().isFormed();
    }

    /** Спрятать груду блоков после освящения и рисовать цельную модель (горн, пресс, Кузня). Верфь — нет. */
    default boolean hidesMembers() {
        return false;
    }

    /** Чем освящают машину. По умолчанию — Омниссианским ключом; машины главы 1 — пустой рукой. */
    default boolean formsWith(ItemStack stack) {
        return stack.getItem() instanceof OmnissianKeyItem;
    }

    /** Всё, что нельзя ломать, пока машина собрана: её блоки и то, что она построила. */
    default List<BlockPos> protectedPositions() {
        return multiblock().members();
    }

    /** Можно ли сейчас разобрать машину ключом; при отказе машина сама объясняет игроку почему. */
    default boolean canUnform(ServerPlayer player) {
        return true;
    }

    /** Кто освятил машину — например, чтобы засчитать квест. */
    default void onFormedBy(ServerPlayer player) {
    }

    default void onFormed(ServerLevel level) {
    }

    default void onUnformed(ServerLevel level) {
    }

    default void tickFormed(ServerLevel level) {
    }
}
