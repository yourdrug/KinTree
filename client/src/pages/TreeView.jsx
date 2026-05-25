/**
 * pages/TreeView.jsx
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, Link }          from "react-router-dom";
import { motion, AnimatePresence }  from "framer-motion";
import { Leaf, ChevronLeft, UserPlus, Share2 } from "lucide-react";
import { Button }     from "@/components/ui/button";
import { toast }      from "@/components/ui/use-toast";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import TreeCanvas     from "@/components/tree/TreeCanvas";
import PersonSidebar  from "@/components/tree/PersonSidebar";
import AddPersonModal from "@/components/tree/AddPersonModal";
import {
  personsApi,
  relationsApi,
  loadFamilyTree,
  createPersonAsChild,
  createPersonAsSpouse,
  createPersonAsSibling,
  getPersonRelations,
  toPartialDate,
} from "@/api";
import { useAuth }  from "@/lib/AuthContext";
import { ROUTES }   from "@/lib/routes";

export default function TreeView() {
  const { id: familyId } = useParams();
  const { user }         = useAuth();

  const [family,         setFamily]         = useState(null);
  const [nodes,          setNodes]          = useState([]);
  const [edges,          setEdges]          = useState([]);
  const [graph,          setGraph]          = useState(null);
  const [relationMaps,   setRelationMaps]   = useState(new Map());
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [focusPersonId, setFocusPersonId] = useState(null);
  const [loading,        setLoading]        = useState(true);
  const [showModal,      setShowModal]      = useState(false);
  const [relativePerson, setRelativePerson] = useState(null);
  const [editPerson,     setEditPerson]     = useState(null);
  const [isOwner,        setIsOwner]        = useState(false);
  const [modalConnectMode, setModalConnectMode] = useState(false);

  const selectedIdRef = useRef(null);

  // ── Load data ──────────────────────────────────────────────────────────────

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await loadFamilyTree(familyId);
      setFamily(data.family);
      setNodes(data.nodes);
      setEdges(data.edges);
      setGraph(data.graph);
      setRelationMaps(data.relationMaps);

      if (selectedIdRef.current) {
        const updated = data.nodes.find((n) => n.id === selectedIdRef.current);
        setSelectedPerson(updated ?? null);
        if (!updated) selectedIdRef.current = null;
      }
    } catch {
      toast({ variant: "destructive", title: "Ошибка загрузки",
        description: "Не удалось загрузить семейное дерево. Попробуйте обновить страницу." });
    } finally {
      setLoading(false);
    }
  }, [familyId]);

  useEffect(() => { loadData(); }, [loadData]);
  useEffect(() => {
    if (user && family) setIsOwner(family.owner_id === user.id);
  }, [user, family]);

  // ── Person selection ───────────────────────────────────────────────────────

  const handleSelectPerson = useCallback((node) => {
      setFocusPersonId(null);
      setSelectedPerson((prev) => {
      if (prev?.id === node.id) { selectedIdRef.current = null; return null; }
      selectedIdRef.current = node.id;
      return node;
    });
  }, []);

  const handleCloseSidebar = useCallback(() => {
    setSelectedPerson(null);
    selectedIdRef.current = null;
  }, []);

  // ── Modal ──────────────────────────────────────────────────────────────────

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

  const openConnect = useCallback((person) => {
    setEditPerson(person);
    setRelativePerson(null);
    setModalConnectMode(true);
    setShowModal(true);
  }, []);

  const closeModal = useCallback(() => {
    setShowModal(false);
    setRelativePerson(null);
    setEditPerson(null);
    setModalConnectMode(false);
  }, []);

  // ── Connect existing persons ───────────────────────────────────────────────

  const handleConnect = useCallback(async ({ personA, personB, relType, marriageDate, divorceDate }) => {
    try {
      if (relType === "spouse") {
        await relationsApi.addSpouse({
          person_a_id: personA,
          person_b_id: personB,
          marriage_status: "MARRIED",
          marriage_year:   marriageDate ? parseInt(marriageDate) : null,
          divorce_year:    divorceDate  ? parseInt(divorceDate)  : null,
        });
      } else if (relType === "parent_child_ab") {
        await relationsApi.addParentChild({ parent_id: personA, child_id: personB, relation_type: "BIOLOGICAL" });
      } else if (relType === "parent_child_ba") {
        await relationsApi.addParentChild({ parent_id: personB, child_id: personA, relation_type: "BIOLOGICAL" });
      } else if (relType === "sibling") {
        const relA = getPersonRelations(relationMaps, personA);
        const relB = getPersonRelations(relationMaps, personB);
        const sharedParents = relA.parentIds.filter(id => relB.parentIds.includes(id));
        if (sharedParents.length === 0 && relA.parentIds.length === 0 && relB.parentIds.length === 0) {
          toast({ title: "Братья/сёстры связаны", description: "У обоих нет родителей — добавьте общего родителя вручную." });
        }
        toast({ title: "Для связи братьев/сестёр", description: "Убедитесь, что у них есть общий родитель в дереве." });
        await loadData();
        return;
      }
      toast({ title: "Связь создана" });
      await loadData();
    } catch (err) {
      const message = err?.response?.data?.message || err?.response?.data?.detail || err?.message || "Проверьте данные.";
      toast({ variant: "destructive", title: "Ошибка создания связи",
        description: typeof message === "string" ? message : "Неизвестная ошибка." });
      throw err;
    }
  }, [familyId, loadData, relationMaps]);

  // ── Save ───────────────────────────────────────────────────────────────────

  const handleSave = useCallback(async (formData, existingId, relationType, relPerson, extra = {}) => {
    const personPayload = {
      first_name: formData.first_name?.trim() || null,
      last_name:  formData.last_name?.trim()  || null,
      gender:     formData.gender || "MALE",
      birth_date: toPartialDate(formData.birth_date),
      death_date: toPartialDate(formData.death_date),
      family_id:  familyId,
    };

    try {
      // ── Edit existing person ─────────────────────────────────────────────
      if (existingId) {
        const { family_id: _fid, ...patchPayload } = personPayload;
        await personsApi.patch(existingId, patchPayload);
        toast({ title: "Изменения сохранены" });
        await loadData();
        return;
      }

      let newPerson = null;

      // ── Add without relation ─────────────────────────────────────────────
      if (!relPerson || !relationType) {
        newPerson = await personsApi.create(personPayload);

      // ── Add as child ─────────────────────────────────────────────────────
      } else if (relationType === "child") {
        newPerson = await createPersonAsChild(personPayload, relPerson.id);

        if (extra.secondParentId) {
          await relationsApi.addParentChild({
            parent_id: extra.secondParentId,
            child_id:  newPerson.id,
            relation_type: "BIOLOGICAL",
          });

          if (extra.parentsMarried) {
            try {
              await relationsApi.addSpouse({
                person_a_id:     relPerson.id,
                person_b_id:     extra.secondParentId,
                marriage_status: "MARRIED",
                marriage_year:   extra.marriageDate ? parseInt(extra.marriageDate) : null,
                divorce_year:    extra.divorceDate  ? parseInt(extra.divorceDate)  : null,
              });
            } catch {
              // Already spouses — ignore duplicate
            }
          }
        }

      // ── Add as parent ────────────────────────────────────────────────────
      } else if (relationType === "parent") {
        newPerson = await personsApi.create(personPayload);
        await relationsApi.addParentChild({
          parent_id:     newPerson.id,
          child_id:      relPerson.id,
          relation_type: "BIOLOGICAL",
        });

        // ── NEW: link new parent as spouse of existing co-parent ──────────
        if (extra.makeSpouseOfCoParent && extra.coParentId) {
          try {
            await relationsApi.addSpouse({
              person_a_id:     newPerson.id,
              person_b_id:     extra.coParentId,
              marriage_status: "MARRIED",
              marriage_year:   extra.coParentMarriageDate ? parseInt(extra.coParentMarriageDate) : null,
              divorce_year:    extra.coParentDivorceDate  ? parseInt(extra.coParentDivorceDate)  : null,
            });
          } catch {
            // Already spouses — ignore duplicate, but warn user
            toast({
              title: "Связь супругов уже существует",
              description: "Эти два человека уже были отмечены как партнёры.",
            });
          }
        }

      // ── Add as partner ───────────────────────────────────────────────────
      } else if (relationType === "partner") {
        newPerson = await createPersonAsSpouse(personPayload, relPerson.id);

      // ── Add as sibling ───────────────────────────────────────────────────
      } else if (relationType === "sibling") {
        const relPersonRelations = getPersonRelations(relationMaps, relPerson.id);
        const { siblingParentMode, siblingParentId } = extra;

        if (siblingParentMode === "different" && siblingParentId) {
          newPerson = await personsApi.create(personPayload);
          await relationsApi.addParentChild({
            parent_id:     siblingParentId,
            child_id:      newPerson.id,
            relation_type: "BIOLOGICAL",
          });
        } else {
          newPerson = await createPersonAsSibling(personPayload, relPersonRelations.parentIds, "BIOLOGICAL");

          if (relPersonRelations.parentIds.length === 0) {
            toast({ title: "Брат/сестра добавлен(а)",
              description: "У выбранной персоны нет родителей — добавьте общего родителя вручную." });
            await loadData();
            return;
          }
        }
      }

      toast({ title: "Человек добавлен" });
      if (newPerson?.id) setFocusPersonId(newPerson.id);
      await loadData();
    } catch (err) {
      const message = err?.response?.data?.message || err?.response?.data?.detail || err?.message || "Проверьте данные и попробуйте снова.";
      toast({ variant: "destructive", title: "Ошибка сохранения",
        description: typeof message === "string" ? message : "Неизвестная ошибка." });
      throw err;
    }
  }, [familyId, loadData, relationMaps]);

  // ── Delete ─────────────────────────────────────────────────────────────────

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

  // ── Render ─────────────────────────────────────────────────────────────────

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

  console.log(focusPersonId)
  console.log(nodes[0]?.id)

  return (
    <div className="fixed inset-0 flex flex-col">
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
          {!user            && <span className="text-sm text-muted-foreground px-2">Гость</span>}
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

      <div className="flex-1 flex relative overflow-hidden">
        <TreeCanvas
          nodes={nodes}
          edges={edges}
          selectedPerson={selectedPerson}
          onSelectPerson={handleSelectPerson}
          canEdit={isOwner}
          onAddChild={(parent) => openAdd(parent)}
          focusPersonId={focusPersonId ?? nodes[0]?.id}
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
                onConnect={openConnect}
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
        initialConnectMode={modalConnectMode}
        onSave={handleSave}
        onConnect={handleConnect}
        relativePerson={relativePerson}
        editPerson={editPerson}
        relationMaps={relationMaps}
        nodes={nodes}
      />
    </div>
  );
}
