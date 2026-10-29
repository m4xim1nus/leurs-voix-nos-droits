<!-- Sources citées à l'appui d'un jugement, affichées à côté de lui (règle de CLAUDE.md). -->
<script lang="ts">
  import { date } from '$lib/format';
  import type { Source } from '$lib/types';

  let { sources }: { sources: Source[] } = $props();
</script>

{#if sources.length}
  <ul class="sources">
    {#each sources as s (s.id)}
      <li>
        <a href={s.url} rel="external">{s.titre}</a>
        <span class="discret"
          >{s.auteur}{#if s.date}, {date(s.date)}{/if}</span
        >
      </li>
    {/each}
  </ul>
{/if}

<style>
  .sources {
    margin: 0.4rem 0 0;
    padding-left: 1.1rem;
    font-size: 0.93rem;
  }
  .sources li {
    margin-bottom: 0.25rem;
  }
  .sources span::before {
    content: ' ';
  }
</style>
