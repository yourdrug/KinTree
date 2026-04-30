// client/src/pages/TreeView.jsx
// Uses the new API layer. "tree" = Family, "members" = Persons, relations via relationsApi.

import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Leaf, ChevronLeft, UserPlus, Share2, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import TreeCanvas from "../components/tree/TreeCanvas";
import PersonSidebar from "../components/tree/PersonSidebar";
import AddPersonModal from "../components/tree/AddPersonModal";
import {
  familiesApi,
  personsApi,
  relationsApi,
  loadFamilyTree,
  createPersonAsChild,
  createPersonAsSpouse,
} from "@/api";
import { useAuth } from "@/lib/AuthContext";

export default function TreeView() {
  const { id: familyId } = useParams();
  const { user } = useAuth();

  const [family, setFamily] = useState(null);
  const [persons, setPersons] = useState([]);   // flat list for sidebar / canvas
  const [graph, setGraph] = useState(null);     // { nodes, edges, meta }
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [relativePerson, setRelativePerson] = useState(null); // link target
  const [editPerson, setEditPerson] = useState(null);
  const [isOwner, setIsOwner] = useState(false);

  // ── Load ──────────────────────────────────────────────────────────────────

  useEffect(() => {
    loadData();
  }, [familyId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const { family, persons, graph } = await loadFamilyTree(familyId);
      setFamily(family);
      setPersons(persons);
      setGraph(graph);
    } catch (err) {
      console.error("Load family tree failed:", err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── Ownership ─────────────────────────────────────────────────────────────

  useEffect(() => {
    if (user && family) {
      setIsOwner(family.owner_id === user.id);
    }
  }, [user, family]);

  // Keep selectedPerson in sync when persons list updates
  useEffect(() => {
    if (selectedPerson) {
      const updated = persons.find((p) => p.id === selectedPerson.id);
      if (updated) setSelectedPerson(updated);
    }
  }, [persons]);

  // ── Modal helpers ─────────────────────────────────────────────────────────

  const openAdd = (relative = null) => {
    setRelativePerson(relative);
    setEditPerson(null);
    setShowModal(true);
  };

  const openEdit = (person) => {
    setEditPerson(person);
    setRelativePerson(null);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setRelativePerson(null);
    setEditPerson(null);
  };

  // ── Save (create / update) ────────────────────────────────────────────────

  /**
   * Called by AddPersonModal.
   *
   * @param {Object} data         - Person fields
   * @param {string|null} existingId - If set, PATCH instead of POST
   * @param {"parent"|"child"|"partner"|null} relationType
   * @param {Person|null} relPerson   - The person to link to
   */
  const handleSave = async (data, existingId, relationType, relPerson) => {
    try {
      if (existingId) {
        // ── Edit existing person ──────────────────────────────────────────
        const updated = await personsApi.patch(existingId, data);
        setPersons((prev) => prev.map((p) => (p.id === existingId ? updated : p)));
        return;
      }

      // ── Create new person, then wire up relation ──────────────────────
      const personPayload = { ...data, family_id: familyId };

      if (relationType === "child" && relPerson) {
        // relPerson is the parent
        await createPersonAsChild(personPayload, relPerson.id);
      } else if (relationType === "parent" && relPerson) {
        // new person is parent of relPerson
        const newPerson = await personsApi.create(personPayload);
        await relationsApi.addParentChild({
          parent_id: newPerson.id,
          child_id: relPerson.id,
        });
      } else if (relationType === "partner" && relPerson) {
        await createPersonAsSpouse(personPayload, relPerson.id);
      } else {
        // No relation — just create
        await personsApi.create(personPayload);
      }

      // Reload full tree so graph + persons stay in sync
      await loadData();
    } catch (err) {
      console.error("Save person failed:", err.message);
    }
  };

  // ── Delete person ─────────────────────────────────────────────────────────

  const handleDelete = async (personId) => {
    try {
      await personsApi.delete(personId);
      setPersons((prev) => prev.filter((p) => p.id !== personId));
      if (selectedPerson?.id === personId) setSelectedPerson(null);
      // Reload graph edges (relations are cascade-deleted server-side)
      const updatedGraph = await relationsApi.getGraph(familyId);
      setGraph(updatedGraph);
    } catch (err) {
      console.error("Delete person failed:", err.message);
    }
  };

  // ── Remove relation ───────────────────────────────────────────────────────

  const handleRemoveRelation = async (type, idA, idB) => {
    try {
      if (type === "parent_child") {
        await relationsApi.removeParentChild(idA, idB);
      } else if (type === "spouse") {
        await relationsApi.removeSpouse(idA, idB);
      }
      const updatedGraph = await relationsApi.getGraph(familyId);
      setGraph(updatedGraph);
    } catch (err) {
      console.error("Remove relation failed:", err.message);
    }
  };

  // ── Toggle public visibility ──────────────────────────────────────────────

  const togglePublic = async () => {
    // Family doesn't have is_public in the current backend schema.
    // If you add it, patch here:
    // const updated = await familiesApi.patch(familyId, { is_public: !family.is_public });
    // setFamily(updated);
    console.warn("is_public is not part of the current Family schema.");
  };

  // ── Render ────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center">
        Загрузка...
      </div>
    );
  }

  if (!family) {
    return (
      <div className="fixed inset-0 flex items-center justify-center">
        Семья не найдена
      </div>
    );
  }

  return (
    <div className="fixed inset-0 flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 h-14 border-b">
        <div className="flex items-center gap-3">
          <Link to="/dashboard">
            <Button variant="ghost" size="sm">
              <ChevronLeft className="w-4 h-4" /> Назад
            </Button>
          </Link>
          <span className="font-semibold">{family.name}</span>
          <span className="text-sm text-muted-foreground">
            {graph?.meta?.node_count ?? persons.length} чел.
          </span>
        </div>

        <div className="flex gap-2">
          {!user && <span className="text-sm text-muted-foreground">Гость</span>}
          {user && !isOwner && <span className="text-sm text-muted-foreground">Просмотр</span>}
          {isOwner && (
            <>
              <Button variant="outline" size="sm" onClick={togglePublic}>
                <Share2 className="w-4 h-4" />
              </Button>
              <Button size="sm" onClick={() => openAdd(null)}>
                <UserPlus className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
      </header>

      {/* Canvas + Sidebar */}
      <div className="flex-1 flex relative overflow-hidden">
        <TreeCanvas
          members={persons}
          graph={graph}
          selectedPerson={selectedPerson}
          onSelectPerson={(p) =>
            setSelectedPerson((prev) => (prev?.id === p.id ? null : p))
          }
          canEdit={isOwner}
          onAddChild={(parent) => openAdd(parent)}
        />

        <AnimatePresence>
          {selectedPerson && (
            <motion.div
              initial={{ x: 320 }}
              animate={{ x: 0 }}
              exit={{ x: 320 }}
              className="absolute right-0 top-0 bottom-0 w-80"
            >
              <PersonSidebar
                person={selectedPerson}
                members={persons}
                graph={graph}
                onClose={() => setSelectedPerson(null)}
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

      {/* Add / Edit Modal */}
      <AddPersonModal
        open={showModal}
        onClose={closeModal}
        onSave={handleSave}
        familyId={familyId}
        relativePerson={relativePerson}
        editPerson={editPerson}
      />
    </div>
  );
}
