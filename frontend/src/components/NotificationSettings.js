import React, { useEffect, useState } from "react";
import { getNotificationSettings, setNotificationSettings } from "../api";
import { Form, Button } from "react-bootstrap";

export default function NotificationSettings() {
  const [settings, setSettings] = useState({ pushbullet_token: "", enable: false });

  const loadSettings = async () => {
    const res = await getNotificationSettings();
    setSettings(res.data);
  };

  useEffect(() => { loadSettings(); }, []);

  const handleSave = async () => {
    await setNotificationSettings(settings);
    alert("Notification settings saved.");
  };

  return (
    <div>
      <h5>Pushbullet Notifications</h5>
      <Form.Check
        type="switch"
        label="Enable notifications"
        checked={settings.enable}
        onChange={e => setSettings({...settings, enable: e.target.checked})}
      />
      <Form.Control className="mt-2" placeholder="Pushbullet Access Token" value={settings.pushbullet_token} onChange={e=>setSettings({...settings, pushbullet_token: e.target.value})} />
      <Button className="mt-2" onClick={handleSave}>Save</Button>
    </div>
  );
}
