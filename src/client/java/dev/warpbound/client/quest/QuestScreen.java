package dev.warpbound.client.quest;

import dev.warpbound.Warpbound;
import dev.warpbound.network.QuestBookOpenedPayload;
import dev.warpbound.player.PlayerProgress;
import dev.warpbound.quest.Criterion;
import dev.warpbound.quest.QuestChapter;
import dev.warpbound.quest.QuestDef;
import dev.warpbound.quest.Reward;
import dev.warpbound.quest.StoryFlags;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.resources.sounds.SimpleSoundInstance;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Журнал памяти: окно квестов. Слева главы, в центре карта квестов, справа запись выбранного квеста.
 * Карту можно двигать мышью.
 */
public class QuestScreen extends Screen {
    private static final ResourceLocation BG = Warpbound.id("textures/gui/quest/background.png");
    private static final ResourceLocation NODE_DONE = Warpbound.id("textures/gui/quest/node_done.png");
    private static final ResourceLocation NODE_OPEN = Warpbound.id("textures/gui/quest/node_open.png");
    private static final ResourceLocation NODE_LOCKED = Warpbound.id("textures/gui/quest/node_locked.png");

    private static final int MAX_CELL = 38, MIN_CELL = 28, NODE = 24, TAB_H = 22;
    private static final int GOLD = 0xFFC9A227, GOLD_DIM = 0xFF6A5224, TEXT = 0xFFD8CFC0, MUTED = 0xFF8A8278;
    private static final int GREEN = 0xFF6FE08A, LINE_DONE = 0xFFC9A227, LINE_LOCKED = 0xFF3A3632;

    /** Выбор главы и квеста переживает закрытие окна. */
    private static ResourceLocation lastChapter;
    private static ResourceLocation lastQuest;

    private ResourceLocation chapterId;
    private ResourceLocation selected;
    private String sealedText;
    private double panX, panY;
    private int detailScroll, maxScroll;
    private boolean dragging;

    private int x0, y0, w, h, mx0, my0, mx1, my1, dx0, dx1;

    public QuestScreen() {
        super(Component.literal("Журнал памяти"));
    }

    @Override
    protected void init() {
        w = Math.min(width - 12, 460);
        h = Math.min(height - 12, 280);
        x0 = (width - w) / 2;
        y0 = (height - h) / 2;
        mx0 = x0 + 122;
        my0 = y0 + 34;
        dx1 = x0 + w - 16;
        dx0 = dx1 - Math.max(124, w / 4 + 16);
        mx1 = dx0 - 6;
        my1 = y0 + h - 18;

        List<Map.Entry<ResourceLocation, QuestChapter>> chapters = ClientQuestState.visibleChapters();
        if (chapterId == null) {
            chapterId = lastChapter != null && chapters.stream().anyMatch(e -> e.getKey().equals(lastChapter))
                    ? lastChapter : chapters.stream().filter(e -> !e.getValue().sealed()).map(Map.Entry::getKey).findFirst().orElse(null);
            selected = lastQuest;
        }
        if (!ClientQuestState.progress().has(StoryFlags.OPENED_QUEST_BOOK)) {
            ClientPlayNetworking.send(QuestBookOpenedPayload.INSTANCE);
        }
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        g.blit(BG, x0, y0, w, h, 0, 0, 512, 320, 512, 320);

        QuestChapter chapter = chapterId == null ? null : ClientQuestState.chapter(chapterId).orElse(null);
        Component title = Component.literal(chapter == null ? "Журнал памяти" : chapter.title()).withStyle(ChatFormatting.BOLD);
        g.drawCenteredString(font, title, x0 + w / 2, y0 + 20, GOLD);

        renderTabs(g, mouseX, mouseY);
        frame(g, mx0, my0, mx1, my1, 0x70000000);
        frame(g, dx0, my0, dx1, my1, 0xC0100C0A);
        ResourceLocation hovered = renderMap(g, mouseX, mouseY);
        renderDetail(g);

        if (hovered != null) {
            List<Component> tip = new ArrayList<>();
            tip.add(Component.literal(ClientQuestState.quests().get(hovered).title()).withStyle(ChatFormatting.GOLD));
            tip.add(Component.literal(stateText(hovered)).withStyle(ChatFormatting.GRAY));
            g.renderComponentTooltip(font, tip, mouseX, mouseY);
        }
    }

    private void frame(GuiGraphics g, int ax, int ay, int bx, int by, int fill) {
        g.fill(ax, ay, bx, by, fill);
        g.renderOutline(ax - 1, ay - 1, bx - ax + 2, by - ay + 2, 0xFF5A4520);
    }

    // ------------------------------------------------------------- главы

    private void renderTabs(GuiGraphics g, int mouseX, int mouseY) {
        int y = my0;
        for (Map.Entry<ResourceLocation, QuestChapter> e : ClientQuestState.visibleChapters()) {
            QuestChapter c = e.getValue();
            boolean active = e.getKey().equals(chapterId);
            boolean hover = inside(mouseX, mouseY, x0 + 16, y, mx0 - 6, y + TAB_H - 2);
            int bg = active ? 0xC04A1010 : hover ? 0x80302020 : 0x60000000;
            g.fill(x0 + 16, y, mx0 - 6, y + TAB_H - 2, bg);
            if (active) g.fill(x0 + 16, y, x0 + 18, y + TAB_H - 2, GOLD);
            g.blit(ClientQuestState.iconTexture(c.icon()), x0 + 20, y + 2, 16, 16, 0, 0, 32, 32, 32, 32);
            Component name = c.sealed()
                    ? Component.literal(c.title()).withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.STRIKETHROUGH)
                    : Component.literal(c.title());
            List<FormattedCharSequence> lines = font.split(name, mx0 - 6 - (x0 + 40) - 2);
            int ty = y + (lines.size() > 1 ? 2 : 7);
            for (int i = 0; i < Math.min(2, lines.size()); i++) {
                g.drawString(font, lines.get(i), x0 + 40, ty + i * 9, active ? GOLD : TEXT, false);
            }
            y += TAB_H;
        }
    }

    // ------------------------------------------------------------- карта

    private ResourceLocation renderMap(GuiGraphics g, int mouseX, int mouseY) {
        if (chapterId == null) return null;
        List<Map.Entry<ResourceLocation, QuestDef>> quests = chapterQuests();
        if (quests.isEmpty()) return null;

        Layout l = layout(quests);
        int ox = l.ox(), oy = l.oy(), cell = l.cell();

        PlayerProgress progress = ClientQuestState.progress();
        Map<ResourceLocation, QuestDef> all = ClientQuestState.quests();
        g.enableScissor(mx0, my0, mx1, my1);

        // связи рисуются под узлами
        for (var e : quests) {
            QuestDef q = e.getValue();
            for (ResourceLocation parentId : q.parents()) {
                QuestDef p = all.get(parentId);
                if (p == null || !p.chapter().equals(chapterId)) continue;
                int color = progress.done(parentId) ? LINE_DONE : LINE_LOCKED;
                int ax = ox + p.x() * cell + NODE / 2, ay = oy + p.y() * cell + NODE / 2;
                int bx = ox + q.x() * cell + NODE / 2, by = oy + q.y() * cell + NODE / 2;
                int mid = (ax + bx) / 2;
                g.fill(Math.min(ax, mid), ay - 1, Math.max(ax, mid) + 1, ay + 1, color);
                g.fill(mid - 1, Math.min(ay, by), mid + 1, Math.max(ay, by) + 1, color);
                g.fill(Math.min(mid, bx), by - 1, Math.max(mid, bx) + 1, by + 1, color);
            }
        }

        ResourceLocation hovered = null;
        long pulse = System.currentTimeMillis() / 120 % 20;
        for (var e : quests) {
            QuestDef q = e.getValue();
            int nx = ox + q.x() * cell, ny = oy + q.y() * cell;
            boolean done = progress.done(e.getKey());
            boolean open = !done && ClientQuestState.available(q);
            if (open && pulse < 10) g.fill(nx - 2, ny - 2, nx + NODE + 2, ny + NODE + 2, 0x30C02020);
            g.blit(done ? NODE_DONE : open ? NODE_OPEN : NODE_LOCKED, nx, ny, NODE, NODE, 0, 0, 32, 32, 32, 32);
            if (!done && !open) g.setColor(0.35f, 0.35f, 0.38f, 1f);
            g.blit(ClientQuestState.iconTexture(q.icon()), nx + 4, ny + 4, 16, 16, 0, 0, 32, 32, 32, 32);
            g.setColor(1f, 1f, 1f, 1f);
            if (e.getKey().equals(selected)) g.renderOutline(nx - 3, ny - 3, NODE + 6, NODE + 6, GOLD);
            if (inside(mouseX, mouseY, nx, ny, nx + NODE, ny + NODE) && inside(mouseX, mouseY, mx0, my0, mx1, my1)) {
                hovered = e.getKey();
            }
        }
        g.disableScissor();
        return hovered;
    }

    /** Раскладка карты: шаг сетки подстраивается, чтобы глава влезла по ширине. */
    private record Layout(int ox, int oy, int cell) {
    }

    private Layout layout(List<Map.Entry<ResourceLocation, QuestDef>> quests) {
        int minX = quests.stream().mapToInt(e -> e.getValue().x()).min().orElse(0);
        int maxX = quests.stream().mapToInt(e -> e.getValue().x()).max().orElse(0);
        int minY = quests.stream().mapToInt(e -> e.getValue().y()).min().orElse(0);
        int maxY = quests.stream().mapToInt(e -> e.getValue().y()).max().orElse(0);
        int cell = maxX > minX ? (mx1 - mx0 - NODE - 16) / (maxX - minX) : MAX_CELL;
        cell = Math.max(MIN_CELL, Math.min(MAX_CELL, cell));
        int ox = mx0 + ((mx1 - mx0) - ((maxX - minX) * cell + NODE)) / 2 - minX * cell + (int) panX;
        int oy = my0 + ((my1 - my0) - ((maxY - minY) * cell + NODE)) / 2 - minY * cell + (int) panY;
        return new Layout(ox, oy, cell);
    }

    private List<Map.Entry<ResourceLocation, QuestDef>> chapterQuests() {
        return ClientQuestState.quests().entrySet().stream()
                .filter(e -> e.getValue().chapter().equals(chapterId)).toList();
    }

    private String stateText(ResourceLocation id) {
        if (ClientQuestState.progress().done(id)) return "Выполнено";
        return ClientQuestState.available(ClientQuestState.quests().get(id)) ? "Доступно" : "Сначала выполни предыдущие записи";
    }

    // ------------------------------------------------------------- запись квеста

    private void renderDetail(GuiGraphics g) {
        int pad = 6, width = dx1 - dx0 - pad * 2;
        g.enableScissor(dx0, my0, dx1, my1);
        int y = my0 + pad - detailScroll;
        if (sealedText != null) {
            for (FormattedCharSequence line : font.split(Component.literal(sealedText)
                    .withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.ITALIC), width)) {
                g.drawString(font, line, dx0 + pad, y, 0xFFA040C0, false);
                y += 10;
            }
        } else {
            QuestDef q = selected == null ? null : ClientQuestState.quests().get(selected);
            if (q == null || !q.chapter().equals(chapterId)) {
                for (FormattedCharSequence line : font.split(Component.literal("Выбери запись на карте памяти."), width)) {
                    g.drawString(font, line, dx0 + pad, y, MUTED, false);
                    y += 10;
                }
            } else {
                y = renderQuest(g, q, dx0 + pad, y, width);
            }
        }
        g.disableScissor();
        maxScroll = Math.max(0, y + detailScroll - my1 + pad);
    }

    private int renderQuest(GuiGraphics g, QuestDef q, int x, int y, int width) {
        PlayerProgress progress = ClientQuestState.progress();
        boolean done = progress.done(selected);
        for (FormattedCharSequence line : font.split(Component.literal(q.title()).withStyle(ChatFormatting.BOLD), width)) {
            g.drawString(font, line, x, y, GOLD, false);
            y += 10;
        }
        g.fill(x, y + 1, x + width, y + 2, GOLD_DIM);
        y += 6;

        String name = minecraft.player == null ? "" : minecraft.player.getGameProfile().getName();
        for (String paragraph : q.description().replace("{player}", name).split("\n")) {
            for (FormattedCharSequence line : font.split(Component.literal(paragraph), width)) {
                g.drawString(font, line, x, y, TEXT, false);
                y += 10;
            }
            y += 3;
        }

        y += 3;
        g.drawString(font, "Условия", x, y, GOLD, false);
        y += 11;
        for (Criterion c : q.criteria()) {
            boolean ok = done || criterionMet(c, progress);
            String label = c.label().orElseGet(() -> c.item().map(i -> i.getDescription().getString()).orElse(c.type()));
            if (c.type().equals(Criterion.ITEM) && !done && minecraft.player != null) {
                int have = Math.min(c.count(), minecraft.player.getInventory().countItem(c.item().orElseThrow()));
                label += " " + have + "/" + c.count();
            } else if (c.count() > 1) {
                label += " ×" + c.count();
            }
            for (FormattedCharSequence line : font.split(Component.literal((ok ? "✔ " : "• ") + label), width)) {
                g.drawString(font, line, x, y, ok ? GREEN : MUTED, false);
                y += 10;
            }
        }

        if (!q.rewards().isEmpty()) {
            y += 4;
            g.drawString(font, "Награда", x, y, GOLD, false);
            y += 11;
            int rx = x;
            for (Reward r : q.rewards()) {
                ItemStack stack = r.stack();
                g.renderItem(stack, rx, y);
                g.renderItemDecorations(font, stack, rx, y);
                rx += 20;
            }
            y += 18;
        }
        if (done) {
            y += 2;
            g.drawString(font, "Выполнено", x, y, GREEN, false);
            y += 10;
        }
        return y;
    }

    private boolean criterionMet(Criterion c, PlayerProgress progress) {
        return switch (c.type()) {
            case Criterion.FLAG -> progress.has(c.flag().orElseThrow());
            case Criterion.ITEM -> minecraft.player != null
                    && minecraft.player.getInventory().countItem(c.item().orElseThrow()) >= c.count();
            default -> false;
        };
    }

    // ------------------------------------------------------------- ввод

    @Override
    public boolean mouseClicked(double mouseX, double mouseY, int button) {
        if (button == 0) {
            int y = my0;
            for (Map.Entry<ResourceLocation, QuestChapter> e : ClientQuestState.visibleChapters()) {
                if (inside(mouseX, mouseY, x0 + 16, y, mx0 - 6, y + TAB_H - 2)) {
                    selectChapter(e.getKey(), e.getValue());
                    return true;
                }
                y += TAB_H;
            }
            if (inside(mouseX, mouseY, mx0, my0, mx1, my1)) {
                ResourceLocation hit = nodeAt(mouseX, mouseY);
                if (hit != null) {
                    selected = lastQuest = hit;
                    detailScroll = 0;
                    click();
                } else {
                    dragging = true;
                }
                return true;
            }
        }
        return super.mouseClicked(mouseX, mouseY, button);
    }

    private void selectChapter(ResourceLocation id, QuestChapter c) {
        if (c.sealed()) {
            sealedText = c.sealedText();
            minecraft.getSoundManager().play(SimpleSoundInstance.forUI(SoundEvents.AMBIENT_SOUL_SAND_VALLEY_MOOD.value(), 0.7f, 0.8f));
            return;
        }
        sealedText = null;
        chapterId = lastChapter = id;
        selected = null;
        panX = panY = 0;
        detailScroll = 0;
        click();
    }

    private ResourceLocation nodeAt(double mouseX, double mouseY) {
                List<Map.Entry<ResourceLocation, QuestDef>> quests = chapterQuests();
        if (quests.isEmpty()) return null;
        Layout l = layout(quests);
        for (var e : quests) {
            int nx = l.ox() + e.getValue().x() * l.cell(), ny = l.oy() + e.getValue().y() * l.cell();
            if (inside(mouseX, mouseY, nx, ny, nx + NODE, ny + NODE)) return e.getKey();
        }
        return null;
    }

    @Override
    public boolean mouseDragged(double mouseX, double mouseY, int button, double dragX, double dragY) {
        if (dragging && button == 0) {
            panX += dragX;
            panY += dragY;
            return true;
        }
        return super.mouseDragged(mouseX, mouseY, button, dragX, dragY);
    }

    @Override
    public boolean mouseReleased(double mouseX, double mouseY, int button) {
        dragging = false;
        return super.mouseReleased(mouseX, mouseY, button);
    }

    @Override
    public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
        if (inside(mouseX, mouseY, dx0, my0, dx1, my1)) {
            detailScroll = (int) Math.max(0, Math.min(maxScroll, detailScroll - scrollY * 10));
            return true;
        }
        return super.mouseScrolled(mouseX, mouseY, scrollX, scrollY);
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (QuestKeys.OPEN.matches(keyCode, scanCode)) {
            onClose();
            return true;
        }
        return super.keyPressed(keyCode, scanCode, modifiers);
    }

    private void click() {
        minecraft.getSoundManager().play(SimpleSoundInstance.forUI(SoundEvents.BOOK_PAGE_TURN, 1f));
    }

    private static boolean inside(double x, double y, int ax, int ay, int bx, int by) {
        return x >= ax && x < bx && y >= ay && y < by;
    }
}
