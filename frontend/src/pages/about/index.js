import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const About = ({ updateOrders, orders }) => {
  
  return <Main>
    <MetaTags>
      <title>О проекте</title>
      <meta name="description" content="Фудграм - О проекте" />
      <meta property="og:title" content="О проекте" />
    </MetaTags>
    
    <Container>
      <h1 className={styles.title}>Привет!</h1>
      <div className={styles.content}>
        <div>
          <h2 className={styles.subtitle}>Что это за сайт?</h2>
          <div className={styles.text}>
            <p className={styles.textItem}>
              Фудграм — это сайт, на котором пользователи публикуют свои рецепты, добавляют чужие рецепты в избранное и подписываются на публикации других авторов.
            </p>
            <p className={styles.textItem}>
              Зарегистрированным пользователям доступен сервис «Список покупок» — он позволяет собрать список продуктов, которые нужно купить для приготовления выбранных блюд, и скачать его одним файлом.
            </p>
            <p className={styles.textItem}>
              Чтобы использовать все возможности сайта — нужна регистрация. Проверка адреса электронной почты не осуществляется, вы можете ввести любой email.
            </p>
            <p className={styles.textItem}>
              Заходите и делитесь своими любимыми рецептами!
            </p>
          </div>
        </div>
        <aside>
          <h2 className={styles.additionalTitle}>
            Ссылки
          </h2>
          <div className={styles.text}>
            <p className={styles.textItem}>
              Код проекта находится тут - <a href="https://github.com/madminji/foodgram" className={styles.textLink} target="_blank" rel="noopener noreferrer">Github</a>
            </p>
            <p className={styles.textItem}>
              Автор проекта: <a href="https://github.com/madminji" className={styles.textLink} target="_blank" rel="noopener noreferrer">Минджиао</a>
            </p>
          </div>
        </aside>
      </div>

    </Container>
  </Main>
}

export default About

