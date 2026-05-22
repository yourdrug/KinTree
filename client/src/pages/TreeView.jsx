/**
 * pages/TreeView.jsx
 *
 * ИСПРАВЛЕНИЯ:
 * 1. loadFamilyTree возвращает { family, graph, nodes, relationMaps }.
 *    nodes (graph.nodes) используются как members — содержат generation.
 *    PersonResponse больше не используется для отображения.
 * 2. handleSave "sibling": parentIds берётся из relationMaps (не person.parent_ids).
 * 3. TreeCanvas получает nodes и edges (из graph) — не persons.
 * 4. PersonSidebar получает nodes и relationMaps.
 * 5. selectedPerson хранит NodeResponse (из nodes), синхронизируется через selectedIdRef.
 * 6. handleSave "parent": создаём персону, потом parent_child (не наоборот).
 * 7. Исправлены все useCallback deps.
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, Link }          from "react-router-dom";
import { motion, AnimatePresence }  from "framer-motion";
import { Leaf, ChevronLeft, UserPlus, Share2 } from "lucide-react";
import { Button }      from "@/components/ui/button";
import { toast }       from "@/components/ui/use-toast";
import LoadingSpinner  from "@/components/common/LoadingSpinner";
import TreeCanvas      from "@/components/tree/TreeCanvas";
import PersonSidebar   from "@/components/tree/PersonSidebar";
import AddPersonModal  from "@/components/tree/AddPersonModal";
import {
  personsApi,
  relationsApi,
  loadFamilyTree,
  createPersonAsChild,
  createPersonAsSpouse,
  getPersonRelations,
  toPartialDate,
} from "@/api";
import { useAuth }  from "@/lib/AuthContext";
import { ROUTES }   from "@/lib/routes";

export default function TreeView() {
  const { id: familyId } = useParams();
  const { user }         = useAuth();

  const [family,         setFamily]         = useState(null);
  const [nodes,          setNodes]          = useState([]);      // graph.nodes (NodeResponse)
  const [edges,          setEdges]          = useState([]);      // graph.edges
  const [graph,          setGraph]          = useState(null);    // полный граф для meta
  const [relationMaps,   setRelationMaps]   = useState(new Map());
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [loading,        setLoading]        = useState(true);
  const [showModal,      setShowModal]      = useState(false);
  const [relativePerson, setRelativePerson] = useState(null);
  const [editPerson,     setEditPerson]     = useState(null);
  const [isOwner,        setIsOwner]        = useState(false);

  // Ref для обновления selectedPerson без бесконечного цикла
  const selectedIdRef = useRef(null);

  // ── Загрузка данных ─────────────────────────────────────────────────────
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await loadFamilyTree(familyId);

      setFamily(data.family);
      setNodes(data.nodes);
      setEdges(data.graph?.edges ?? []);
      setGraph(data.graph);
      setRelationMaps(data.relationMaps);

      // Синхронизируем selectedPerson если он был выбран
      if (selectedIdRef.current) {
        const updated = data.nodes.find((n) => n.id === selectedIdRef.current);
        setSelectedPerson(updated ?? null);
        if (!updated) selectedIdRef.current = null;
      }
    } catch {
      toast({
        variant: "destructive",
        title: "Ошибка загрузки",
        description: "Не удалось загрузить семейное дерево. Попробуйте обновить страницу.",
      });
    } finally {
      setLoading(false);
    }
  }, [familyId]);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    if (user && family) setIsOwner(family.owner_id === user.id);
  }, [user, family]);

  // ── Выбор персоны ───────────────────────────────────────────────────────
  const handleSelectPerson = useCallback((node) => {
    setSelectedPerson((prev) => {
      if (prev?.id === node.id) {
        selectedIdRef.current = null;
        return null;
      }
      selectedIdRef.current = node.id;
      return node;
    });
  }, []);

  const handleCloseSidebar = useCallback(() => {
    setSelectedPerson(null);
    selectedIdRef.current = null;
  }, []);

  // ── Модалка ─────────────────────────────────────────────────────────────
  const openAdd  = useCallback((relative = null) => {
    setRelativePerson(relative);
    setEditPerson(null);
    setShowModal(true);
  }, []);

  const openEdit = useCallback((person) => {
    setEditPerson(person);
    setRelativePerson(null);
    setShowModal(true);
  }, []);

  const closeModal = useCallback(() => {
    setShowModal(false);
    setRelativePerson(null);
    setEditPerson(null);
  }, []);

  // ── Сохранение ──────────────────────────────────────────────────────────
  const handleSave = useCallback(async (formData, existingId, relationType, relPerson) => {
    // formData: { first_name, last_name, gender, birth_date: "YYYY-MM-DD"|"", death_date: "...|"" }

    const personPayload = {
      first_name: formData.first_name?.trim() || null,
      last_name:  formData.last_name?.trim()  || null,
      gender:     formData.gender || "MALE",
      birth_date: toPartialDate(formData.birth_date),
      death_date: toPartialDate(formData.death_date),
      family_id:  familyId,
    };

    try {
      if (existingId) {
        // PATCH — для редактирования не передаём family_id
        const { family_id: _fid, ...patchPayload } = personPayload;
        await personsApi.patch(existingId, patchPayload);
        toast({ title: "Изменения сохранены" });
        await loadData();
        return;
      }

      // ── Создание ────────────────────────────────────────────────────────
      if (!relPerson || !relationType) {
        // Без привязки — просто создаём
        await personsApi.create(personPayload);

      } else if (relationType === "child") {
        // relPerson — родитель нового человека
        await createPersonAsChild(personPayload, relPerson.id);

      } else if (relationType === "parent") {
        // relPerson — ребёнок нового человека
        const newPerson = await personsApi.create(personPayload);
        await relationsApi.addParentChild({
          parent_id:     newPerson.id,
          child_id:      relPerson.id,
          relation_type: "BIOLOGICAL",
        });

      } else if (relationType === "partner") {
        await createPersonAsSpouse(personPayload, relPerson.id);

      } else if (relationType === "sibling") {
        // FIX: parentIds берётся из relationMaps — не из relPerson.parent_ids
        const relPersonRelations = getPersonRelations(relationMaps, relPerson.id);
        await relationsApi.addSiblingViaParents(
          personPayload,
          relPersonRelations.parentIds,
          "BIOLOGICAL"
        );

        if (relPersonRelations.parentIds.length === 0) {
          toast({
            title: "Брат/сестра добавлен(а)",
            description: "У выбранной персоны нет родителей — связь сиблингов не создана автоматически. Добавьте общего родителя вручную.",
          });
          await loadData();
          return;
        }
      }

      toast({ title: "Человек добавлен" });
      await loadData();
    } catch (err) {
      // Пробрасываем чтобы AddPersonModal мог оставаться открытым
      const message =
        err?.response?.data?.message ||
        err?.response?.data?.detail  ||
        err?.message                 ||
        "Проверьте данные и попробуйте снова.";
      toast({
        variant: "destructive",
        title:   "Ошибка сохранения",
        description: typeof message === "string" ? message : "Неизвестная ошибка.",
      });
      throw err; // AddPersonModal.handleSave ловит это и не закрывает модалку
    }
  }, [familyId, loadData, relationMaps]);

  // ── Удаление ────────────────────────────────────────────────────────────
  const handleDelete = useCallback(async (personId) => {
    try {
      await personsApi.delete(personId);
      if (selectedIdRef.current === personId) {
        setSelectedPerson(null);
        selectedIdRef.current = null;
      }
      toast({ title: "Запись удалена" });
      await loadData();
    } catch {
      toast({ variant: "destructive", title: "Ошибка удаления", description: "Не удалось удалить запись." });
    }
  }, [loadData]);

  const handleRemoveRelation = useCallback(async (type, idA, idB) => {
    try {
      if (type === "parent_child") await relationsApi.removeParentChild(idA, idB);
      else if (type === "spouse")  await relationsApi.removeSpouse(idA, idB);
      toast({ title: "Связь удалена" });
      await loadData();
    } catch {
      toast({ variant: "destructive", title: "Ошибка", description: "Не удалось удалить связь." });
    }
  }, [loadData]);

  // ── Render ───────────────────────────────────────────────────────────────
  if (loading) return <LoadingSpinner fullScreen />;

  if (!family) {
    return (
      <div className="fixed inset-0 flex flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground">Семья не найдена</p>
        <Link to={ROUTES.dashboard()}>
          <Button variant="outline" className="rounded-xl">← На главную</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 h-14 border-b bg-background/95 backdrop-blur z-20">
        <div className="flex items-center gap-3">
          <Link to={ROUTES.dashboard()}>
            <Button variant="ghost" size="sm" className="rounded-lg gap-1">
              <ChevronLeft className="w-4 h-4" /> Назад
            </Button>
          </Link>
          <div className="w-px h-5 bg-border" />
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-primary flex items-center justify-center">
              <Leaf className="w-3 h-3 text-primary-foreground" />
            </div>
            <span className="font-semibold text-foreground">{family.name}</span>
          </div>
          <span className="text-sm text-muted-foreground">
            {graph?.meta?.node_count ?? nodes.length} чел.
          </span>
        </div>

        <div className="flex gap-2">
          {!user           && <span className="text-sm text-muted-foreground px-2">Гость</span>}
          {user && !isOwner && <span className="text-sm text-muted-foreground px-2">Просмотр</span>}
          {isOwner && (
            <>
              <Button variant="outline" size="sm" className="rounded-lg">
                <Share2 className="w-4 h-4" />
              </Button>
              <Button size="sm" className="rounded-lg gap-1.5" onClick={() => openAdd(null)}>
                <UserPlus className="w-4 h-4" /> Добавить
              </Button>
            </>
          )}
        </div>
      </header>

      {/* Main */}
      <div className="flex-1 flex relative overflow-hidden">
        <TreeCanvas
          nodes={nodes}
          edges={edges}
          selectedPerson={selectedPerson}
          onSelectPerson={handleSelectPerson}
          canEdit={isOwner}
          onAddChild={(parent) => openAdd(parent)}
        />

        <AnimatePresence>
          {selectedPerson && (
            <motion.div
              initial={{ x: 320 }}
              animate={{ x: 0 }}
              exit={{ x: 320 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="absolute right-0 top-0 bottom-0 w-80 z-10"
            >
              <PersonSidebar
                person={selectedPerson}
                nodes={nodes}
                relationMaps={relationMaps}
                onClose={handleCloseSidebar}
                canEdit={isOwner}
                onEdit={openEdit}
                onDelete={handleDelete}
                onAddRelative={(p) => openAdd(p)}
                onRemoveRelation={handleRemoveRelation}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AddPersonModal
        open={showModal}
        onClose={closeModal}
        onSave={handleSave}
        relativePerson={relativePerson}
        editPerson={editPerson}
        relationMaps={relationMaps}
      />
    </div>
  );
}
