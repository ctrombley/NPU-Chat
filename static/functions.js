function saveName(input, chatId) {
    const newName = input.value;
    const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
    const nameSpan = chatElement.querySelector('.chat-name');
    const emojiSpan = chatElement.querySelector('.chat-emoji');
    fetch(`/chats/${chatId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName })
    })
    .then(resp => resp.json())
    .then(data => {
        if (data.name !== undefined) {
            nameSpan.textContent = data.name;
            nameSpan.addEventListener('click', () => switchChat(chatId));
            nameSpan.addEventListener('dblclick', function() {
                if (chatId.startsWith('chat-')) return;
                const input = document.createElement('input');
                input.type = 'text';
                input.value = this.textContent;
                input.style.width = '100%';
                this.replaceWith(input);
                input.focus();
                input.addEventListener('blur', () => saveName(input, chatId));
                input.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') {
                        saveName(input, chatId);
                    }
                });
            });
            input.replaceWith(nameSpan);
        }
    })
    .catch(() => {
        input.replaceWith(nameSpan);
    });
}

function saveEmoji(input, chatId) {
    const newEmoji = input.value;
    const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
    const emojiSpan = chatElement.querySelector('.chat-emoji');
    const nameSpan = chatElement.querySelector('.chat-name');
    fetch(`/chats/${chatId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emoji: newEmoji })
    })
    .then(resp => resp.json())
    .then(data => {
        if (data.emoji !== undefined) {
            emojiSpan.textContent = data.emoji;
            emojiSpan.addEventListener('dblclick', function() {
                if (chatId.startsWith('chat-')) return;
                const input = document.createElement('input');
                input.type = 'text';
                input.value = this.textContent;
                input.style.maxWidth = '20px';
                this.replaceWith(input);
                input.focus();
                input.addEventListener('blur', () => saveEmoji(input, chatId));
                input.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') {
                        saveEmoji(input, chatId);
                    }
                });
            });
            input.replaceWith(emojiSpan);
        }
    })
    .catch(() => {
        input.replaceWith(emojiSpan);
    });
}

/*
MIT License

Copyright (c) 2024 av1d - https://github.com/av1d/

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

/*
   place cursor in the input_text area on page load
*/
document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('input_text').focus();
});

/*
   auto-expand the text input area
*/
function autoExpand(textarea) {
    // Reset textarea height to default in case it shrinks
    textarea.style.height = 'auto';
    // Calculate the height of the content and limit it to 20vw
    const maxHeight = 15 * (window.innerWidth / 100); // Convert 15vw to pixels
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = newHeight + 'px';
}

/*
   handle form submission, start animation. this will also
   listen for a response from npu_server then append the messages
   to the chat dialog and hide the animation once a message is
   received
*/
const chatMessages = document.getElementById('chat-messages');
const form = document.getElementById('user-input');
const loader = document.querySelector('.loader');
const loaderBefore = document.querySelector('.loader:before');
const pupil = document.querySelector('.pupil');
const sendIcon = document.querySelector('.send-icon');

form.addEventListener('submit', function(event) {
    event.preventDefault();

    // Generate a random hash
    const randomHash = Math.random().toString(36).substring(2, 34);

    let url = '/search';
    if (currentChatId && currentChatId.startsWith('chat-')) {
        url += `?session_id=${encodeURIComponent(currentChatId)}`;
    }

    fetch(url, {
        method: 'POST',
        body: new FormData(form)
    })
    .then(response => response.json())
    .then(data => {
        const newResponse = document.createElement('div');
        newResponse.classList.add('message', 'received');
        newResponse.setAttribute('id', randomHash);
        // The server returns HTML-wrapped markdown (<md>...</md>). Insert it as raw HTML
        // instead of wrapping it in a <p> which would break the custom tag rendering.
        newResponse.innerHTML = data.content; // content = json key
        chatMessages.appendChild(newResponse);

        // If server returned a session_id, migrate local chat to use it and update UI name
        if (data.session_id) {
            const serverSid = data.session_id;

            // If currentChatId exists and differs from serverSid, migrate messages and update storage
            if (currentChatId && currentChatId !== serverSid) {
                // Move messages from temporary local chat to server session id
                if (!chats[serverSid]) {
                    chats[serverSid] = chats[currentChatId] || [];
                } else {
                    // append messages to existing server-side mapped chat
                    chats[serverSid] = chats[serverSid].concat(chats[currentChatId] || []);
                }
                // Remove old local chat id
                delete chats[currentChatId];
                saveChatsToStorage();

                // Update chat list UI element to use serverSid as data-chat-id
                const oldElem = document.querySelector(`[data-chat-id="${currentChatId}"]`);
                if (oldElem) {
                    oldElem.dataset.chatId = serverSid;
                }

                currentChatId = serverSid;
                localStorage.setItem('currentChatId', serverSid);
            }

            // Fetch server chat metadata (name + emoji) and update UI label
            fetch(`/chats`)
                .then(resp => resp.json())
                .then(chatListData => {
                    const serverChat = chatListData.find(c => c.id === serverSid);
                    if (serverChat) {
                        const elem = document.querySelector(`[data-chat-id="${serverSid}"]`);
                        if (elem) {
                            const nameSpan = elem.querySelector('.chat-name');
                            if (nameSpan) {
                                nameSpan.textContent = serverChat.name || nameSpan.textContent;
                                const emojiSpan = elem.querySelector('.chat-emoji');
                                if (emojiSpan) {
                                    emojiSpan.textContent = serverChat.emoji || '';
                                }
                            }
                        }
                    }
                })
                .catch(() => {
                    // ignore failures to fetch metadata
                });
        }

        // Save received message to current chat
        if (currentChatId && chats[currentChatId]) {
            chats[currentChatId].push({
                type: 'received',
                text: data.content,
                timestamp: Date.now()
            });
            saveChatsToStorage();
        }

        // Call the renderMarkdown() function of Markdown-Tag
        renderMarkdown(newResponse);

        // Create and insert copy button
        const copyBtn = document.createElement('button');
        copyBtn.setAttribute('id', 'copyBtn');
        copyBtn.setAttribute('class', 'copy-button');
        copyBtn.setAttribute('onclick', 'copyDivContents(this.parentElement.id)');
        copyBtn.innerHTML = '&#x2398;';
        copyBtn.addEventListener('click', function() {
            copyAnswerResponseContent(this);
        });
        newResponse.appendChild(copyBtn);

        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Hide loader and loader:before and unhide send-icon
        // this stops the animation
        loader.style.display = 'none';
        pupil.style.display = 'none';
        if (loaderBefore) {
            loaderBefore.style.display = 'none';
        }
        sendIcon.style.display = 'block';
    })
    .catch(error => {
        console.error('Error:', error);
        const failedMessage = document.createElement('div');
        failedMessage.classList.add('message', 'received');
        failedMessage.innerHTML = '<p>Failed to fetch. Is the server for this UI offline?</p>';
        chatMessages.appendChild(failedMessage);

        // Save error message to current chat
        if (currentChatId && chats[currentChatId]) {
            chats[currentChatId].push({
                type: 'received',
                text: 'Failed to fetch. Is the server for this UI offline?',
                timestamp: Date.now()
            });
            saveChatsToStorage();
        }

        // Hide loader and loader:before and unhide send-icon
        // this stops the animation
        loader.style.display = 'none';
        pupil.style.display = 'none';
        if (loaderBefore) {
            loaderBefore.style.display = 'none';
        }
        sendIcon.style.display = 'block';
    });

    document.getElementById('input_text').value = '';
});

/*Functionality for managing chats*/
const chatList = document.getElementById('chat-list');
const newChatButton = document.getElementById('new-chat-button');
const chats = {}; // Store chat histories here.
let currentChatId = null;

// Load chats from localStorage on page load
function loadChatsFromStorage() {
    const storedChats = localStorage.getItem('chats');
    if (storedChats) {
        const parsedChats = JSON.parse(storedChats);
        Object.assign(chats, parsedChats);

        // Recreate chat list UI
        for (const chatId in chats) {
            addChatToUI(chatId);
        }
    }
}

// Save chats to localStorage
function saveChatsToStorage() {
    localStorage.setItem('chats', JSON.stringify(chats));
}

// Create a new chat ID
function generateChatId() {
    return `chat-${Date.now()}`;
}

// Add chat to the UI
function addChatToUI(chatId) {
    const chatElement = document.createElement('li');
    chatElement.className = 'chat-item';
    chatElement.dataset.chatId = chatId;

    const emojiSpan = document.createElement('span');
    emojiSpan.className = 'chat-emoji';
    emojiSpan.textContent = '';

    const chatName = document.createElement('span');
    chatName.className = 'chat-name';
    chatName.textContent = `Chat ${Object.keys(chats).length}`;
    chatName.addEventListener('click', () => switchChat(chatElement.dataset.chatId));

    // Make name editable on double-click
    chatName.addEventListener('dblclick', function() {
        if (chatId.startsWith('chat-')) return; // Only allow editing for server chats
        const input = document.createElement('input');
        input.type = 'text';
        input.value = this.textContent;
        input.style.width = '100%';
        this.replaceWith(input);
        input.focus();
        input.addEventListener('blur', () => saveName(input, chatId));
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                saveName(input, chatId);
            }
        });
    });

    // Make emoji editable on double-click
    emojiSpan.addEventListener('dblclick', function() {
        if (chatId.startsWith('chat-')) return; // Only allow editing for server chats
        const input = document.createElement('input');
        input.type = 'text';
        input.value = this.textContent;
        input.style.maxWidth = '20px';
        this.replaceWith(input);
        input.focus();
        input.focus();
        input.addEventListener('blur', () => saveEmoji(input, chatId));
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                saveEmoji(input, chatId);
            }
        });
    });

    const deleteButton = document.createElement('button');
    deleteButton.className = 'delete-chat';
    deleteButton.textContent = '×';
    deleteButton.title = 'Delete chat';
    deleteButton.addEventListener('click', (e) => {
        e.stopPropagation();
        deleteChat(chatId);
    });

    chatElement.appendChild(emojiSpan);
    chatElement.appendChild(chatName);
    chatElement.appendChild(deleteButton);
    chatList.appendChild(chatElement);
}

function switchChat(chatId) {
    if (!chats[chatId]) return;

    // Save current chat ID to localStorage
    localStorage.setItem('currentChatId', chatId);

    currentChatId = chatId;
    chatMessages.innerHTML = '';

    // Mark active chat
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-chat-id="${chatId}"]`).classList.add('active');

    // Load messages for this chat
    chats[chatId].forEach(message => {
        const newMessage = document.createElement('div');
        newMessage.className = `message ${message.type}`;
        // If this is a received message that already contains HTML (server-provided), insert as HTML
        if (message.type === 'received' && /<\w+/.test(message.text)) {
            newMessage.innerHTML = message.text;
        } else {
            // For plain text (sent messages or received fallback), escape and wrap in a <p>
            const p = document.createElement('p');
            p.textContent = message.text;
            newMessage.appendChild(p);
        }
        chatMessages.appendChild(newMessage);
    });

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addChat(chatId) {
    chats[chatId] = [];
    addChatToUI(chatId);
    saveChatsToStorage();
}

function deleteChat(chatId) {
    if (!chats[chatId]) return;

    // Remove from storage
    delete chats[chatId];
    saveChatsToStorage();

    // Remove from UI
    const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (chatElement) {
        chatElement.remove();
    }

    // If this was the current chat, switch to another chat or create new one
    if (currentChatId === chatId) {
        const remainingChats = Object.keys(chats);
        if (remainingChats.length > 0) {
            switchChat(remainingChats[0]);
        } else {
            // Create a new chat if no chats remain
            const newChatId = generateChatId();
            addChat(newChatId);
            switchChat(newChatId);
        }
        localStorage.removeItem('currentChatId');
    }
}

// Initialize chat management
document.addEventListener('DOMContentLoaded', function() {
    // Load existing chats
    loadChatsFromStorage();

    // If no chats exist, create the first one
    if (Object.keys(chats).length === 0) {
        const firstChatId = generateChatId();
        addChat(firstChatId);
        switchChat(firstChatId);
    } else {
        // Restore the last active chat or switch to first available
        const lastChatId = localStorage.getItem('currentChatId');
        if (lastChatId && chats[lastChatId]) {
            switchChat(lastChatId);
        } else {
            switchChat(Object.keys(chats)[0]);
        }
    }
});

newChatButton.addEventListener('click', () => {
    const chatId = generateChatId();
    addChat(chatId);
    switchChat(chatId);
});

/*
    behavior for text entry (enter to send, allow shift+enter for newline)
*/
const inputTextElement = document.getElementById('input_text');
const sendButton = document.querySelector('.send-button');

inputTextElement.addEventListener('keydown', function(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendButton.click();
  }
});

/*
   behaviors for sent message
*/
sendButton.addEventListener('click', function() {
    const inputText = inputTextElement.value.trim();

    if (inputText) {
        const newMessage = document.createElement('div');
        newMessage.textContent = inputText;
        newMessage.classList.add('message', 'sent');
        chatMessages.appendChild(newMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Save sent message to current chat
        if (currentChatId && chats[currentChatId]) {
            chats[currentChatId].push({
                type: 'sent',
                text: inputText,
                timestamp: Date.now()
            });
            saveChatsToStorage();
        }

        const sendIcon = document.querySelector('.send-icon');
        sendIcon.style.display = 'none';

        const loaderDivs = document.querySelectorAll('.loader, .loader:before, .pupil');
        loaderDivs.forEach(div => div.style.display = 'block');

        form.dispatchEvent(new Event('submit'));

        inputTextElement.style.height = 'auto';
        inputTextElement.value = ''; // Clear the textarea after sending
    }
});

/*
   copy button behavior (copy text + animation)
*/
function copyDivContents(divId) {
  const div = document.getElementById(divId);
  const mdElement = div.querySelector('md');
  const mdText = mdElement.textContent;
  const tempInput = document.createElement('textarea');

  tempInput.value = mdText;
  document.body.appendChild(tempInput);

  tempInput.select();
  document.execCommand('copy');

  document.body.removeChild(tempInput);

  const button = document.getElementById('copyBtn');
  button.classList.add('animate');
  setTimeout(() => {
    button.classList.remove('animate');
  }, 1000);

  console.log('Copied text:', mdText);
}
