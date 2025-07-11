document.getElementById('language-form').addEventListener('submit', async (event) => {
    event.preventDefault();

    const word = document.getElementById('word-input').value;
    const foreignLanguage = document.getElementById('foreign-language-select').value;

    if (!word || !foreignLanguage) {
        alert('Please enter both a word and select a foreign language.');
        return;
    }

    const response = await fetch('http://localhost:5001/api/lesson', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ word, foreignLanguage })
    });

    const data = await response.json();

    if (response.ok) {
        displayFlashcards(data);
    } else {
        alert(`Error: ${data.error}`);
    }
});

function displayFlashcards(lesson) {
    const flashcardContainer = document.getElementById('flashcard-container');
    flashcardContainer.innerHTML = ''; // Clear previous content

    const flashcardDiv = document.createElement('div');
    flashcardDiv.className = 'flashcard';

    // Direct Translation
    const directTranslation = document.createElement('section');
    const directTransTitle = document.createElement('h2');
    directTransTitle.textContent = 'Direct Translation';
    const directTranslationText = document.createElement('p');
    directTranslationText.textContent = lesson.directTranslation;
    directTranslation.appendChild(directTransTitle);
    directTranslation.appendChild(directTranslationText);

    // Related Vocabulary
    const relatedVocab = document.createElement('section');
    const vocabTitle = document.createElement('h2');
    vocabTitle.textContent = 'Related Vocabulary';
    lesson.relatedVocabulary.forEach(item => {
        const vocabItem = document.createElement('p');
        vocabItem.textContent = `${item.vocabulary} - ${item.translation}`;
        relatedVocab.appendChild(vocabItem);
    });
    relatedVocab.insertBefore(vocabTitle, relatedVocab.firstChild);

    // Practical Usage
    const practicalUsage = document.createElement('section');
    const usageTitle = document.createElement('h2');
    usageTitle.textContent = 'Practical Usage';
    lesson.practicalUsage.forEach(item => {
        const usageItem = document.createElement('p');
        usageItem.textContent = `${item.usage} - ${item.translation}`;
        practicalUsage.appendChild(usageItem);
    });
    practicalUsage.insertBefore(usageTitle, practicalUsage.firstChild);

    // Advanced Content
    const advancedContent = document.createElement('section');
    const advTitle = document.createElement('h2');
    advTitle.textContent = 'Advanced Content';
    const advContentText = document.createElement('p');
    advContentText.textContent = lesson.advancedContent.content;
    const advExplanation = document.createElement('p');
    advExplanation.textContent = lesson.advancedContent.explanation;
    advancedContent.appendChild(advTitle);
    advancedContent.appendChild(advContentText);
    advancedContent.appendChild(advExplanation);

    // Append all sections to the flashcard div
    flashcardDiv.appendChild(directTranslation);
    flashcardDiv.appendChild(relatedVocab);
    flashcardDiv.appendChild(practicalUsage);
    flashcardDiv.appendChild(advancedContent);

    // Append the flashcard div to the container
    flashcardContainer.appendChild(flashcardDiv);
}