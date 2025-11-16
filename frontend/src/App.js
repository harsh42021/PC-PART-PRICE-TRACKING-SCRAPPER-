
import React, { useEffect, useState } from "react";
import { getBuilds, addBuild } from "./api";
import BuildTab from "./components/BuildTab";
import RetailerManager from "./components/RetailerManager";
import NotificationSettings from "./components/NotificationSettings";
import { Container, Row, Col, Button, Modal, Form } from "react-bootstrap";

export default function App() {
  const [builds, setBuilds] = useState([]);
  const [selectedBuild, setSelectedBuild] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newBuildName, setNewBuildName] = useState("");

  const loadBuilds = async () => {
    const res = await getBuilds();
    setBuilds(res.data);
    if (!selectedBuild && res.data.length > 0) setSelectedBuild(res.data[0]);
  };

  useEffect(() => { loadBuilds(); }, []);

  const handleAddBuild = async () => {
    if (newBuildName.trim() === "") return;
    await addBuild({ name: newBuildName });
    setShowAddModal(false);
    setNewBuildName("");
    loadBuilds();
  };

  return (
    <Container fluid>
      <Row className="mt-3">
        <Col md={3}>
          <Button variant="primary" onClick={() => setShowAddModal(true)}>Add Build</Button>
          <hr />
          <RetailerManager />
          <hr />
          <NotificationSettings />
        </Col>
        <Col md={9}>
          {selectedBuild && <BuildTab build={selectedBuild} />}
        </Col>
      </Row>

      <Modal show={showAddModal} onHide={() => setShowAddModal(false)}>
        <Modal.Header closeButton><Modal.Title>Add Build</Modal.Title></Modal.Header>
        <Modal.Body>
          <Form.Control
            placeholder="Build name"
            value={newBuildName}
            onChange={(e) => setNewBuildName(e.target.value)}
          />
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAddModal(false)}>Cancel</Button>
          <Button variant="primary" onClick={handleAddBuild}>Add</Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}
