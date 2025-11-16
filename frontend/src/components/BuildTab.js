import React, { useEffect, useState } from "react";
import { getBuildParts, addBuildPart, deleteBuildPart, getProductUrls, addProductUrl, deleteProductUrl, refreshPrices, getPriceHistory } from "../api";
import { Table, Button, Form, Modal } from "react-bootstrap";

const CATEGORIES = ["CPU","GPU","CPU Cooler","Case","Motherboard","Power Supply","Case Fans","DDR5 Memory","NVME","AIO Liquid Cooler"];

export default function BuildTab({ build }) {
  const [parts, setParts] = useState([]);
  const [showAddPartModal, setShowAddPartModal] = useState(false);
  const [newPartCategory, setNewPartCategory] = useState(CATEGORIES[0]);
  const [newPartOEM, setNewPartOEM] = useState("");
  const [newPartLabel, setNewPartLabel] = useState("");

  const loadParts = async () => {
    const res = await getBuildParts(build.id);
    setParts(res.data);
  };

  useEffect(() => { if(build) loadParts(); }, [build]);

  const handleAddPart = async () => {
    if (!newPartOEM) return;
    await addBuildPart(build.id, { category: newPartCategory, oem: newPartOEM, label: newPartLabel });
    setShowAddPartModal(false);
    setNewPartOEM(""); setNewPartLabel("");
    loadParts();
  };

  const handleDeletePart = async (part) => {
    await deleteBuildPart(build.id, { category: part.category, oem: part.oem });
    loadParts();
  };

  return (
    <div>
      <h3>{build.name}</h3>
      <Button variant="success" onClick={() => setShowAddPartModal(true)}>Add Part</Button>
      <Button className="ms-2" variant="primary" onClick={refreshPrices}>Refresh Prices</Button>
      <Table striped bordered hover className="mt-3">
        <thead><tr><th>Category</th><th>OEM</th><th>Label</th><th>Actions</th></tr></thead>
        <tbody>
          {parts.map(p => <tr key={p.id}>
            <td>{p.category}</td>
            <td>{p.oem}</td>
            <td>{p.label}</td>
            <td><Button size="sm" variant="danger" onClick={()=>handleDeletePart(p)}>Delete</Button></td>
          </tr>)}
        </tbody>
      </Table>

      <Modal show={showAddPartModal} onHide={() => setShowAddPartModal(false)}>
        <Modal.Header closeButton><Modal.Title>Add Part</Modal.Title></Modal.Header>
        <Modal.Body>
          <Form.Select value={newPartCategory} onChange={e => setNewPartCategory(e.target.value)}>
            {CATEGORIES.map(c => <option key={c}>{c}</option>)}
          </Form.Select>
          <Form.Control className="mt-2" placeholder="OEM part number" value={newPartOEM} onChange={e=>setNewPartOEM(e.target.value)} />
          <Form.Control className="mt-2" placeholder="Label (optional)" value={newPartLabel} onChange={e=>setNewPartLabel(e.target.value)} />
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={()=>setShowAddPartModal(false)}>Cancel</Button>
          <Button variant="primary" onClick={handleAddPart}>Add</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}
