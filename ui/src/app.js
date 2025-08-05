const config = require('./config');

// Store the current word and language for loading more content
let currentWord = '';
let currentLanguage = '';

document.getElementById('language-form').addEventListener('submit', async (event) => {
    event.preventDefault();

    currentWord = document.getElementById('word-input').value;
    currentLanguage = document.getElementById('foreign-language-select').value;

    if (!currentWord || !currentLanguage) {
        alert('Please enter both a word and select a foreign language.');
        return;
    }

    // Add a loading state for better UX
    const submitButton = event.target.querySelector('button');
    submitButton.disabled = true;
    submitButton.textContent = 'Loading...';

    try {
        const response = await fetch(config.urlContextEngine, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word: currentWord, foreignLanguage: currentLanguage })
        });

        const data = await response.json();

        if (response.ok) {
            loadFlashcards(data, true); // true means it's the initial load
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Failed to fetch lesson:', error);
        alert('An error occurred while fetching the lesson. Please check the console.');
    } finally {
        // Restore button state
        submitButton.disabled = false;
        submitButton.textContent = 'Submit';
    }
});

// Add event listener for the Load More button
document.getElementById('load-more-btn').addEventListener('click', async () => {
    if (!currentWord || !currentLanguage) {
        return;
    }

    const loadMoreBtn = document.getElementById('load-more-btn');
    loadMoreBtn.disabled = true;
    loadMoreBtn.textContent = 'Loading...';

    try {
        const response = await fetch(config.urlContextEngine, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word: currentWord, foreignLanguage: currentLanguage })
        });

        const data = await response.json();

        if (response.ok) {
            loadFlashcards(data, false); // false means it's an extension
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Failed to fetch additional content:', error);
        alert('An error occurred while fetching additional content. Please check the console.');
    } finally {
        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = 'Load More';
    }
});

/**
 * Creates a single flashcard element with a title and content.
 * Content can be a simple string or an array of objects to be formatted.
 * @param {string} title - The title of the flashcard.
 * @param {string|Array<Object>|Object} content - The content for the flashcard.
 * @returns {HTMLDivElement} The created flashcard element.
 */
function createFlashcard(title, content) {
    const flashcardDiv = document.createElement('div');
    flashcardDiv.className = 'flashcard';

    const titleElement = document.createElement('h2');
    titleElement.textContent = title;
    flashcardDiv.appendChild(titleElement);

    if (typeof content === 'string') {
        const contentElement = document.createElement('p');
        contentElement.textContent = content;
        flashcardDiv.appendChild(contentElement);
    } else if (Array.isArray(content)) {
        content.forEach(item => {
            const p = document.createElement('p');
            // Handles both {vocabulary, translation} and {usage, translation} structures
            const mainText = item.vocabulary || item.usage;
            p.textContent = `${mainText} - ${item.translation}`;
            flashcardDiv.appendChild(p);
        });
    } else if (typeof content === 'object' && content !== null) {
        // Handle advancedContent
        const contentText = document.createElement('p');
        contentText.textContent = content.content;
        const explanationText = document.createElement('p');
        explanationText.style.fontStyle = 'italic'; // Differentiate explanation
        explanationText.textContent = content.explanation;
        flashcardDiv.appendChild(contentText);
        flashcardDiv.appendChild(explanationText);
    }

    return flashcardDiv;
}

/**
 * Loads flashcards based on the lesson data.
 * For initial load, clears existing flashcards. For extensions, appends to existing ones.
 * Sets up an IntersectionObserver to animate cards as they scroll into view.
 * @param {object} lesson - The lesson data from the API.
 * @param {boolean} isInitialLoad - Whether this is the first load or an extension.
 */
function loadFlashcards(lesson, isInitialLoad) {
    const flashcardContainer = document.getElementById('flashcard-container');
    
    // For initial load, clear previous content
    if (isInitialLoad) {
        flashcardContainer.innerHTML = '';
    }

    // Define the order and content of the cards
    // For extensions, we skip the direct translation as it would be repetitive
    const cardsData = isInitialLoad 
        ? [
            { title: 'Direct Translation', content: lesson.directTranslation },
            { title: 'Related Vocabulary', content: lesson.relatedVocabulary },
            { title: 'Practical Usage', content: lesson.practicalUsage },
            { title: 'Advanced Content', content: lesson.advancedContent }
        ]
        : [
            { title: 'Related Vocabulary (Extended)', content: lesson.relatedVocabulary },
            { title: 'Practical Usage (Extended)', content: lesson.practicalUsage },
            { title: 'Advanced Content (Extended)', content: lesson.advancedContent }
        ];

    // Create and append all flashcard elements to the DOM
    const cardElements = cardsData
        .filter(cardInfo => cardInfo.content)
        .map(cardInfo => createFlashcard(cardInfo.title, cardInfo.content));

    cardElements.forEach(cardEl => flashcardContainer.appendChild(cardEl));

    // Show the load more button after initial load
    if (isInitialLoad) {
        const loadMoreContainer = document.getElementById('load-more-container');
        // Remove it from its current location and append it to flashcard container
        loadMoreContainer.remove();
        flashcardContainer.appendChild(loadMoreContainer);
        loadMoreContainer.style.display = 'block';
    }

    // To fix the final card getting "stuck" at the bottom, we add extra
    // scrollable space. A padding value of ~80% of the viewport height gives
    // enough "runway" for the last card to scroll completely out of view.
    const allCards = flashcardContainer.querySelectorAll('.flashcard');
    if (allCards.length > 1) {
        flashcardContainer.style.paddingBottom = '2rem';
    } else {
        flashcardContainer.style.paddingBottom = '0';
    }

    // Set up the scroll-triggered animation for the newly created cards
    setupScrollAnimation();
}

/**
 * Initializes an IntersectionObserver to add a 'visible' class to flashcards
 * when they enter the viewport, triggering a one-time animation.
 * This function handles both initial cards and newly added cards.
 */
function setupScrollAnimation() {
    const flashcards = document.querySelectorAll('.flashcard');

    // The first card is visible by default, so we don't need to observe it.
    // This also prevents a "flash" if the observer fires slightly late.
    if (flashcards.length > 0) {
        // Only make the first card visible if it's not already
        if (!flashcards[0].classList.contains('visible')) {
            flashcards[0].classList.add('visible');
        }
    }

    const observerOptions = {
        root: null, // Use the viewport as the root
        rootMargin: '0px',
        // Trigger the animation when a card is 50% visible.
        threshold: 0.5
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            // If the card is intersecting the viewport, make it visible.
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Once a card is visible, we don't need to observe it anymore.
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Start observing each flashcard, skipping the first one.
    // Only observe cards that are not already visible
    flashcards.forEach((card, index) => {
        if (index > 0 && !card.classList.contains('visible')) {
            observer.observe(card);
        }
    });
}