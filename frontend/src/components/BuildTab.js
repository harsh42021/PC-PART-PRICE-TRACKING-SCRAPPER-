// frontend/src/components/BuildTab.js
// CLEANED: removed unused imports, unused functions, and unused variables

import React, { useState, useEffect } from "react";
import axios from "../api";

function BuildTab({ build, onRefresh }) {
  const [parts, setParts] = useState([]);
  const [newCategory, setNewCategory] = useState("");
  const [newOEM, setNewOEM] = useState("");
  const [newLabel, setNewLabel] = useState("");

  useEffect(() => {
    if (build?.id) {
      axios
        .get(`/builds/${build.id}/parts`)
        .then((res) => setParts(res.data))
        .catch(() => {});
    }
  }, [build]);

  const addPart = async () => {
    if (!newCategory || !newOEM) return;

    await axios.post(`/builds/${build.id}/parts`, {
      category: newCategory,
      oem: newOEM,
      label: newLabel,
    });

    const res = await axios.get(`/builds/${build.id}/parts`);
    setParts(res.data);

    setNewCategory("");
    setNewOEM("");
    setNewLabel("");
  };

  const deletePart = async (category, oem) => {
    await axios.delete(`/builds/${build.id}/parts`, {
      data: { category, oem },
    });

    const res = await axios.get(`/builds/${build.id}/parts`);
    setParts(res.data);
  };

  return (
    <div>
      <h3>{build?.name}</h3>

      <h5>Add part</h5>
      <input
        placeholder="Category"
        value={newCategory}
        onChange={(e) => setNewCategory(e.target.value)}
      />
      <input
        placeholder="OEM"
        value={newOEM}
        onChange={(e) => setNewOEM(e.target.value)}
      />
      <input
        placeholder="Label"
        value={newLabel}
        onChange={(e) => setNewLabel(e.target.value)}
      />
      <button onClick={addPart}>Add</button>

      <h4>Parts</h4>
      <ul>
        {parts.map((p) => (
          <li key={p.id}>
            {p.category} – {p.oem} – {p.label}
            <button onClick={() => deletePart(p.category, p.oem)}>X</button>
          </li>
        ))}
      </ul>

      <button onClick={onRefresh}>Refresh Prices</button>
    </div>
  );
}

export default BuildTab;
