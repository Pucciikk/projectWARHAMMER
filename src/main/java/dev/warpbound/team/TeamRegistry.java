package dev.warpbound.team;

import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.saveddata.SavedData;

import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

/**
 * Все отряды мира (data/warpbound_teams.dat в Overworld).
 * Правила из обсуждения: ушедший игрок сохраняет свои исследования, общие остаются у всех,
 * корабль принадлежит лидеру. Смешанные отряды лоялистов и падших разрешены.
 */
public class TeamRegistry extends SavedData {
    private static final String FILE = "warpbound_teams";

    private final Map<UUID, Team> teams = new LinkedHashMap<>();
    private final Map<UUID, UUID> teamOf = new HashMap<>();
    /** Приглашения не переживают перезапуск сервера, и это нормально. */
    private final Map<UUID, UUID> invites = new HashMap<>();

    public static TeamRegistry get(MinecraftServer server) {
        return server.overworld().getDataStorage().computeIfAbsent(
                new SavedData.Factory<>(TeamRegistry::new, TeamRegistry::load, null), FILE);
    }

    /** Отряд игрока; если его нет, создаётся отряд из одного человека. */
    public Team of(UUID player, String playerName) {
        UUID id = teamOf.get(player);
        if (id != null) return teams.get(id);
        return create(player, playerName);
    }

    public Optional<Team> find(UUID player) {
        return Optional.ofNullable(teamOf.get(player)).map(teams::get);
    }

    public Team create(UUID leader, String name) {
        leave(leader);
        Team team = new Team(UUID.randomUUID(), name, leader);
        teams.put(team.id, team);
        teamOf.put(leader, team.id);
        setDirty();
        return team;
    }

    public void invite(Team team, UUID player) {
        invites.put(player, team.id);
    }

    /** Принять приглашение. Возвращает отряд или пусто, если приглашения нет. */
    public Optional<Team> accept(UUID player) {
        UUID id = invites.remove(player);
        Team team = id == null ? null : teams.get(id);
        if (team == null) return Optional.empty();
        leave(player);
        team.members.add(player);
        teamOf.put(player, team.id);
        setDirty();
        return Optional.of(team);
    }

    /** Выйти из отряда. Если ушёл лидер, им становится следующий; пустой отряд удаляется. */
    public void leave(UUID player) {
        UUID id = teamOf.remove(player);
        if (id == null) return;
        Team team = teams.get(id);
        team.members.remove(player);
        if (team.members.isEmpty()) {
            teams.remove(id);
        } else if (team.leader.equals(player)) {
            team.leader = team.members.iterator().next();
        }
        setDirty();
    }

    public Collection<Team> all() {
        return teams.values();
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        ListTag list = new ListTag();
        for (Team team : teams.values()) list.add(team.save());
        tag.put("teams", list);
        return tag;
    }

    private static TeamRegistry load(CompoundTag tag, HolderLookup.Provider registries) {
        TeamRegistry registry = new TeamRegistry();
        for (Tag t : tag.getList("teams", Tag.TAG_COMPOUND)) {
            Team team = Team.load((CompoundTag) t);
            registry.teams.put(team.id, team);
            for (UUID member : team.members) registry.teamOf.put(member, team.id);
        }
        return registry;
    }
}
