import React, { useEffect, useState } from "react";
import { getRetailers, addRetailer, toggleRetailer } from "../api";
import { Table, Button, Form, Modal } from "react-bootstrap";

export default function RetailerManager() {
  const [retailers, setRetailers] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newRetailerName, setNewRetailerName] = useState("");

  const loadRetailers = async () => {
    const res = await getRetailers();
    setRetailers(res.data);
  };

  useEffect(() => { loadRetailers(); }, []);

  const handleAddRetailer = async () => {
    if (!newRetailerName) return;
    await addRetailer({ name: newRetailerName });
    setShowAddModal(false);
    setNewRetailerName("");
    loadRetailers();
  };

  const handleToggle = async (id) => {
    await toggleRetailer(id);
    loadRetailers();
  };

  return (
    <div>
      <h5>Retailers</h5>
      <Button variant="primary" onClick={() => setShowAddModal(true)}>Add Retailer</Button>
      <Table striped bordered hover size="sm" className="mt-2">
        <thead><tr><th>Name</th><th>Active</th><th>Action</th></tr></thead>
        <tbody>
          {retailers.map(r => <tr key={r.id}>
            <td>{r.name}</td>
            <td>{r.active ? "Yes" : "No"}</td>
            <td><Button size="sm" onClick={()=>handleToggle(r.id)}>{r.active ? "Deactivate" : "Activate"}</Button></td>
          </tr>)}
        </tbody>
      </Table>

      <Modal show={showAddModal} onHide={()=>setShowAddModal(false)}>
        <Modal.Header closeButton><Modal.Title>Add Retailer</Modal.Title></Modal.Header>
        <Modal.Body>
          <Form.Control placeholder="Retailer Name" value={newRetailerName} onChange={e=>setNewRetailerName(e.target.value)} />
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={()=>setShowAddModal(false)}>Cancel</Button>
          <Button variant="primary" onClick={handleAddRetailer}>Add</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}
