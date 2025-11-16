const messagesEl = document.getElementById('messages');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('message');
const stepsVal = document.getElementById('stepsVal');
const calVal = document.getElementById('calVal');
const tipBody = document.getElementById('tipBody');
const bmiBox = document.getElementById('bmiBox');

function addMessage(text, who) {
  const div = document.createElement('div');
  div.className = `msg ${who === 'you' ? 'you' : 'bot'}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function computeBmi(weight, height) {
  const h = Number(height) / 100;
  if (!h || h <= 0) return null;
  return Math.round((Number(weight) / (h*h)) * 100) / 100;
}

function updateBmiBox() {
  const weight = document.getElementById('weight').value;
  const height = document.getElementById('height').value;
  const bmi = computeBmi(weight, height);
  bmiBox.textContent = bmi ? `BMI: ${bmi}` : 'BMI: —';
}

['weight','height'].forEach(id => {
  const el = document.getElementById(id);
  el.addEventListener('input', updateBmiBox);
});
updateBmiBox();

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;
  addMessage(text, 'you');
  messageInput.value = '';

  const payload = {
    name: document.getElementById('name').value,
    age: document.getElementById('age').value,
    weight: document.getElementById('weight').value,
    height: document.getElementById('height').value,
    message: text
  };

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.reply) addMessage(data.reply, 'bot');
    if (data.steps_today != null) {
      stepsVal.textContent = data.steps_today;
      calVal.textContent = `${Math.round(data.steps_today * 0.04 * 100) / 100} kcal`;
    }
    if (data.reminder) tipBody.textContent = data.reminder;
    if (data.bmi) bmiBox.textContent = `BMI: ${data.bmi} (${data.bmi_status})`;
  } catch (err) {
    addMessage('Error contacting server. Using offline tips: 7–8h sleep, 7–9k steps/day, protein each meal.', 'bot');
  }
});

